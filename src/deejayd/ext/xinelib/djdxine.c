/*************************************************************************
 * xine_impl.c
 **************************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <Python.h>
#include <xine/video_out.h>
#include <xine/xineutils.h>

#include "djdxine.h"
//#define DJD_DEBUG 1

/***************************************************************************
 *  Callback functions
 *  ************************************************************************/

static void dest_size_callback(void *data, int video_width, int video_height,
        double video_pixel_aspect, int *dest_width, int *dest_height, double
        *dest_pixel_aspect)
{
    _Xine* xine = (_Xine*)data;
    /* Should take video_pixel_aspect into account here... */
    xmutex_lock(xine->frame_info.lock);
    *dest_width = xine->frame_info.width;
    *dest_height = xine->frame_info.height;
    xmutex_unlock(xine->frame_info.lock);
    *dest_pixel_aspect = xine->player.screen_pixel_aspect;
}

static void frame_output_callback(void *data, int video_width,
        int video_height, double video_pixel_aspect, int *dest_x, int *dest_y,
        int *dest_width, int *dest_height, double *dest_pixel_aspect, int
        *win_x, int *win_y)
{
    _Xine* xine = (_Xine*)data;
    *dest_x            = 0;
    *dest_y            = 0;
    xmutex_lock(xine->frame_info.lock);
    *win_x             = xine->frame_info.xpos;
    *win_y             = xine->frame_info.ypos;
    *dest_width        = xine->frame_info.width;
    *dest_height       = xine->frame_info.height;
    xmutex_unlock(xine->frame_info.lock);
    *dest_pixel_aspect = xine->player.screen_pixel_aspect;
}

/***************************************************************************
 *  Internal functions
 *  ************************************************************************/

void* _x11_event_handler(void* xine_obj)
{
    XEvent xevent;
    int got_event;

    _Xine* xine = (_Xine*)xine_obj;
    while (1) {
        XLockDisplay(xine->player.display);
        got_event = XPending(xine->player.display);
        if( got_event )
            XNextEvent(xine->player.display, &xevent);
        XUnlockDisplay(xine->player.display);

        if( !got_event ) {
            xine_usec_sleep(20000);
            continue;
        }

        switch(xevent.type) {
            case Expose:
                if (xevent.xexpose.count != 0)
                    break;
                xine_port_send_gui_data(xine->player.vport,
                    XINE_GUI_SEND_EXPOSE_EVENT, &xevent);
                break;
        }
    }
}

static void _set_video_area(_Xine* xine)
{
    Window root;
    int xpos, ypos;
    unsigned int width, height, border, depth;

    XGetGeometry(xine->player.display,
        xine->player.window[xine->player.fullscreen],
        &root,&xpos,&ypos,&width,&height,&border,&depth);
    xmutex_lock(xine->frame_info.lock);
    xine->frame_info.xpos = xpos;
    xine->frame_info.ypos = ypos;
    xine->frame_info.width = width;
    xine->frame_info.height = height;
    xmutex_unlock(xine->frame_info.lock);
}

static void _hide_cursor(Display* display, Drawable window)
{
    Pixmap bm_no;
    Colormap cmap;
    Cursor no_ptr;
    XColor black, dummy;
    static char bm_no_data[] = {0, 0, 0, 0, 0, 0, 0, 0};

    cmap = DefaultColormap(display, DefaultScreen(display));
    XAllocNamedColor(display, cmap, "black", &black, &dummy);
    bm_no = XCreateBitmapFromData(display, window, bm_no_data, 8, 8);
    no_ptr = XCreatePixmapCursor(display, bm_no, bm_no, &black, &black, 0, 0);

    XDefineCursor(display, window, no_ptr);
    XFreeCursor(display, no_ptr);
    if (bm_no != None)
        XFreePixmap(display, bm_no);
    XFreeColors(display, cmap, &black.pixel, 1, 0);
}

static void _create_windows(_Xine* xine)
{
    int xpos, ypos, width, height;
    MWMHints mwmhints;
    Atom XA_NO_BORDER;
    XSetWindowAttributes attr;

    XLockDisplay(xine->player.display);
    XA_NO_BORDER = XInternAtom(xine->player.display,
                "_MOTIF_WM_HINTS", False);
    mwmhints.flags = MWM_HINTS_DECORATIONS;
    mwmhints.decorations = 0;

    /* create fullscreen window*/
    xine->player.window[1] = XCreateSimpleWindow( xine->player.display,
        XDefaultRootWindow(xine->player.display),0, 0,
        (DisplayWidth(xine->player.display,
        xine->player.screen)), (DisplayHeight(
        xine->player.display, xine->player.screen)), 0, 0, 0);
    XSelectInput(xine->player.display, xine->player.window[1],INPUT_MOTION);
    XChangeProperty(xine->player.display, xine->player.window[1],XA_NO_BORDER,
        XA_NO_BORDER, 32, PropModeReplace,
        (unsigned char *) &mwmhints,PROP_MWM_HINTS_ELEMENTS);
    /* do not manage this window with WM */
    attr.override_redirect = True;
    XChangeWindowAttributes(xine->player.display,xine->player.window[1],
                        CWOverrideRedirect,&attr);
    /* hide cursor */
    _hide_cursor(xine->player.display,xine->player.window[1]);

    /* create normal window */
    xpos    = 0;
    ypos    = 0;
    width   = 640;
    height  = 400;
    xine->player.window[0] = XCreateSimpleWindow( xine->player.display,
                XDefaultRootWindow(xine->player.display),
                xpos,ypos,width,height,1,0,0);
    XSelectInput(xine->player.display, xine->player.window[0],INPUT_MOTION);
    XUnlockDisplay(xine->player.display);

    _set_video_area(xine);
}

static void _destroy_windows(_Xine* xine)
{
    int i;

    XLockDisplay(xine->player.display);
    for (i=0;i<2;i++) {
        XUnmapWindow(xine->player.display, xine->player.window[i]);
        XDestroyWindow(xine->player.display, xine->player.window[i]);
    }
    XSync(xine->player.display, False);
    XUnlockDisplay(xine->player.display);
}

void _djdxine_set_fatal_error(_Xine* xine, char *error)
{
    strcpy(xine->error, error);
}

void _player_reset(_Xine* xine)
{
    xine->playing = 0;
    xine->isvideo = 0;

    xine->player.vport = NULL;
    xine->player.stream = NULL;
    xine->player.event_queue = NULL;
}

/***************************************************************************
 *  Pubic functions
 *  ************************************************************************/
_Xine* djdxine_create(xine_event_listener_cb_t event_callback,
                void* event_callback_data)
{
    _Xine* xine;

    // allocate memory
    xine = (_Xine*)malloc(sizeof(_Xine));
    if(xine == NULL) return NULL;
    xine->frame_info.lock = (xmutex_rec*)malloc(sizeof(xmutex_rec));
    if (xine->frame_info.lock == NULL) {
        free(xine);
        return NULL;
        }
    xine->error = (char *)malloc(sizeof(char)*ERROR_MSG);
    if (xine->error == NULL) {
        free(xine->frame_info.lock);
        free(xine);
        return NULL;
        }
    strcpy(xine->error,"");
    xine->lang = (char *)malloc(sizeof(char)*XINE_LANG_MAX);
    if (xine->lang == NULL) {
        free(xine->error);
        free(xine->frame_info.lock);
        free(xine);
        return NULL;
        }

    //
    // Init structure parm
    //
    _player_reset(xine);
    xmutex_init(xine->frame_info.lock);
    xine->frame_info.xpos = 0;
    xine->frame_info.ypos = 0;
    xine->frame_info.width = 0;
    xine->frame_info.height = 0;

    // init event callback
    xine->event_callback = event_callback;
    xine->event_callback_data = event_callback_data;

    // Create main xine instance
    xine->player.xine = xine_new();
    xine_init(xine->player.xine);

    /* Create a xine instance used for querying data about video files */
    xine->data_mine.xine = xine_new();
    xine_init(xine->data_mine.xine);
    xine->data_mine.aport = xine_open_audio_driver(xine->data_mine.xine,
                                                "none", NULL);
    xine->data_mine.vport = xine_open_video_driver(xine->data_mine.xine,
                                    "none", XINE_VISUAL_TYPE_NONE, NULL);
    xine->data_mine.stream = xine_stream_new(xine->data_mine.xine,
                                xine->data_mine.aport, xine->data_mine.vport);
    xine->data_mine.current_filename = NULL;
    xine->data_mine.file_info.title = NULL;

    return xine;
}

int djdxine_audio_init(_Xine* xine, const char *audio_driver)
{
    // Open audio driver
#ifdef DJD_DEBUG
    printf("DEBUG - Open audio driver %s \n", audio_driver);
#endif
    xine->player.aport = xine_open_audio_driver(xine->player.xine,
                                                audio_driver, NULL);
    if (xine->player.aport == NULL) {
        xine_close_audio_driver(xine->player.xine, xine->player.aport);
        _djdxine_set_fatal_error(xine, "Unable to init audio driver");
        return 1;
        }

    return 0;
}

int djdxine_video_init(_Xine* xine)
{
    // Init video stuff
    if (!XInitThreads()) {
        _djdxine_set_fatal_error(xine, "Unable to init X Threads");
        return 1;
        }

    xine->player.fullscreen = 0;
    return 0;
}

int djdxine_attach(_Xine* xine, const char *video_driver,
                const char* display_name, int is_video)
{
    double screen_width, screen_height;
    x11_visual_t vis;
#ifdef DJD_DEBUG
    printf("DEBUG - Enter attach function \n");
#endif

    if (xine->player.stream != NULL) // already atached
        return -1;

    if (is_video) { // init video stuff
        xine->player.display = XOpenDisplay(display_name);
        if (!xine->player.display) { // Unable to open display
            _djdxine_set_fatal_error(xine, "Unable to open display");
            return 1;
            }
        xine->player.screen = XDefaultScreen(xine->player.display);
        screen_width = (DisplayWidth(xine->player.display,
            xine->player.screen) * 1000 / DisplayWidthMM(
            xine->player.display, xine->player.screen));
        screen_height = (DisplayHeight(xine->player.display,
            xine->player.screen) * 1000 / DisplayHeightMM(
            xine->player.display, xine->player.screen));
        xine->player.screen_pixel_aspect = screen_height / screen_width;

        /* create windows */
        _create_windows(xine);

        /* update video driver and create a new stream */
        vis.display = xine->player.display;
        vis.screen = xine->player.screen;
        vis.d = xine->player.window[xine->player.fullscreen];
        vis.dest_size_cb = dest_size_callback;
        vis.frame_output_cb = frame_output_callback;
        vis.user_data = xine;

#ifdef DJD_DEBUG
    printf("DEBUG - Open video driver %s \n", video_driver);
#endif
        xine->player.vport = xine_open_video_driver(xine->player.xine,
                    video_driver, XINE_VISUAL_TYPE_X11, (void *)&vis);
        if (xine->player.vport == NULL) {
            _destroy_windows(xine);
            XCloseDisplay(xine->player.display);
            _djdxine_set_fatal_error(xine, "Unable to init video driver");
            return 1;
            }
        }
    else {
#ifdef DJD_DEBUG
    printf("DEBUG - Open null video driver \n");
#endif
        xine->player.vport = xine_open_video_driver(xine->player.xine, "none",
                                            XINE_VISUAL_TYPE_NONE, NULL);
        }
    xine->isvideo = is_video;

/***
 * Create player
 **/
    // Init the main stream
    xine->player.stream = xine_stream_new(xine->player.xine,xine->player.aport,
                                            xine->player.vport);
    if (xine->player.stream == NULL) {
        xine_close_audio_driver(xine->player.xine, xine->player.aport);
        xine_close_video_driver(xine->player.xine, xine->player.vport);
        _djdxine_set_fatal_error(xine, "Unable to init the main stream");
        return 1;
        }

    xine->player.event_queue = xine_event_new_queue(xine->player.stream);
    xine_event_create_listener_thread(xine->player.event_queue,
        xine->event_callback,xine->event_callback_data);

#ifdef DJD_DEBUG
    printf("DEBUG - Leave attach function \n");
#endif
    return 0;
}

void djdxine_detach(_Xine* xine)
{
    if (xine->playing) {
        djdxine_stop(xine);
        }

    /* close main player */
    if (xine->player.event_queue)
        xine_event_dispose_queue(xine->player.event_queue);
    if (xine->player.stream)
        xine_dispose(xine->player.stream);
    if (xine->player.vport) {
#ifdef DJD_DEBUG
    printf("DEBUG - Close video Driver \n");
#endif
        xine_close_video_driver(xine->player.xine, xine->player.vport);
        }

    /* close video parm */
    if (xine->isvideo) {
        _destroy_windows(xine);
        XCloseDisplay(xine->player.display);
    }

    _player_reset(xine);
}

void djdxine_destroy(_Xine* xine)
{
    djdxine_detach(xine);
    if (xine->player.aport)
        xine_close_audio_driver(xine->player.xine, xine->player.aport);

    xine_exit(xine->player.xine);

    /* close data mine */
    if (xine->data_mine.current_filename) {
        free (xine->data_mine.current_filename);
        xine_close(xine->data_mine.stream);
    }
    xine_dispose(xine->data_mine.stream);
    xine_close_audio_driver(xine->data_mine.xine, xine->data_mine.aport);
    xine_close_video_driver(xine->data_mine.xine, xine->data_mine.vport);
    xine_exit(xine->data_mine.xine);

    /* free ressource */
    xmutex_clear(xine->frame_info.lock);
    xmutex_free(xine->frame_info.lock);
    free(xine->error);
    free(xine->lang);
    free(xine);
}

void djdxine_load_config(_Xine* xine, const char *filename)
{
#ifdef DJD_DEBUG
    printf("DEBUG - Load config file '%s' \n", filename);
#endif
    xine_config_load(xine->player.xine,filename);
}

int djdxine_set_config_param(_Xine* xine, const char *param_key,
                                    int type, void* value)
{
    xine_cfg_entry_t entry;

    if (!xine_config_lookup_entry (xine->player.xine, param_key, &entry)) {
        printf("Error : unable to set %s\n",param_key);
        return 1;
        }

    if (type == XINE_CONFIG_TYPE_ENUM)
        entry.num_value = *(int *)value;
    else if (type == XINE_CONFIG_TYPE_STRING)
        strcpy(entry.str_value, (char *)value);
    else return 1;
    xine_config_update_entry(xine->player.xine,&entry);

    return 0;
}

int djdxine_play(_Xine* xine, const char* filename, int isvideo, int fullscreen)
{
#ifdef DJD_DEBUG
    printf("DEBUG - Play %s file \n",filename);
#endif
    if (xine->player.stream == NULL) {
        _djdxine_set_fatal_error(xine, "Main stream is not intialized");
        return 1;
        }

    if (xine->playing) djdxine_stop(xine);

    if (isvideo) {
        xine->player.fullscreen = fullscreen;

        XLockDisplay(xine->player.display);
        XMapRaised(xine->player.display,
            xine->player.window[xine->player.fullscreen]);
        XSync(xine->player.display, False);
        XUnlockDisplay(xine->player.display);

        _set_video_area(xine);
        xine_port_send_gui_data(xine->player.vport,
            XINE_GUI_SEND_DRAWABLE_CHANGED,
            (void *) xine->player.window[xine->player.fullscreen]);
        xine_port_send_gui_data(xine->player.vport,
                XINE_GUI_SEND_VIDEOWIN_VISIBLE,(void *) 1);

        /*
         * Create x11 event listener thread
         */
        pthread_create(&(xine->player.xevent_thread),NULL,
                _x11_event_handler, (void *)xine);
    }

    if (!xine_open(xine->player.stream, filename) ||
                   !xine_play(xine->player.stream, 0, 0)) {
        return 1;
        }

    xine->playing = 1;
    return 0;
}

void djdxine_stop(_Xine* xine)
{
    if(!xine->playing) return;

    xine_close(xine->player.stream);
    if (xine->isvideo) {
        /*
         * Stop x11 event listener thread
         */
        pthread_cancel(xine->player.xevent_thread);

        XLockDisplay(xine->player.display);
        XUnmapWindow(xine->player.display,
                     xine->player.window[xine->player.fullscreen]);
        XUnmapWindow(xine->player.display,
                     xine->player.window[0]);
        XUnmapWindow(xine->player.display,
                     xine->player.window[1]);
        XSync(xine->player.display, False);
        XUnlockDisplay(xine->player.display);
    }
    xine->playing = 0;
}

void djdxine_set_playing(_Xine* xine, int is_playing)
{
    if(!xine->playing) return;

    if(is_playing) {
        xine_set_param(xine->player.stream,XINE_PARAM_SPEED,XINE_SPEED_NORMAL);
    } else {
        xine_set_param(xine->player.stream, XINE_PARAM_SPEED, XINE_SPEED_PAUSE);
    }
}

int djdxine_get_status(_Xine* xine)
{
    int status;

    if(!xine->playing) return DJDXINE_STATUS_STOP;
    else {
        status = xine_get_param(xine->player.stream,XINE_PARAM_SPEED);
        if (status == XINE_SPEED_PAUSE)
            return DJDXINE_STATUS_PAUSE;
        else
            return DJDXINE_STATUS_PLAY;
        }
}

void djdxine_set_param(_Xine* xine, int param, int value, int need_playing)
{
    if((!xine->player.stream) || (need_playing && !xine->playing)) return;
    xine_set_param(xine->player.stream,param,value);
}

int djdxine_get_parm(_Xine* xine, int param)
{
    if (!xine->player.stream) return -2;

    return xine_get_param(xine->player.stream,param);
}

void djdxine_seek(_Xine* xine, int position)
{
    if(!xine->playing) return;
    xine_play(xine->player.stream, 0, position);
}

int djdxine_get_position(_Xine* xine)
{
    int pos_stream,pos_time,length_time;

    if(!xine->playing) return -1;

    if (xine_get_pos_length(xine->player.stream,&pos_stream, &pos_time,
                              &length_time)) {
        return pos_time;
        }
    return -1;
}

int djdxine_set_fullscreen(_Xine* xine,int fullscreen)
{
    if ((!xine->playing) || (!xine->isvideo)) return 1;
    if (xine->player.fullscreen == fullscreen) return 0;

    XLockDisplay(xine->player.display);
    XUnmapWindow(xine->player.display,
                 xine->player.window[xine->player.fullscreen]);
    XMapRaised(xine->player.display, xine->player.window[fullscreen]);
    XSync(xine->player.display, False);
    XUnlockDisplay(xine->player.display);

    xine->player.fullscreen = fullscreen;
    _set_video_area(xine);
    xine_port_send_gui_data(xine->player.vport, XINE_GUI_SEND_DRAWABLE_CHANGED,
                (void*) xine->player.window[xine->player.fullscreen]);

    return 0;
}

int djdxine_set_data_mine(_Xine* xine, const char* filename)
{
    int rv;
    if (xine->data_mine.current_filename) {
        if (!strcmp (filename, xine->data_mine.current_filename)) {
            return 2;
            }
        xine_close(xine->data_mine.stream);
        free (xine->data_mine.current_filename);
        xine->data_mine.current_filename = NULL;
        if (xine->data_mine.file_info.title != NULL) {
            free (xine->data_mine.file_info.title);
            xine->data_mine.file_info.title = NULL;
            }
        }
    rv = xine_open(xine->data_mine.stream, filename);
    if (rv)
        xine->data_mine.current_filename = strdup(filename);
    return rv;
}

FileInfo *djdxine_file_info(_Xine* xine, const char* filename)
{
    int rv;
    int duration;
    int dummy, dummy2;
    rv = djdxine_set_data_mine(xine, filename);
    if (rv == 0)
        return NULL;
    if (rv == 1) {
        xine_get_pos_length(xine->data_mine.stream,&dummy, &dummy2, &duration);
        xine->data_mine.file_info.duration = duration;
        xine->data_mine.file_info.width = xine_get_stream_info(
            xine->data_mine.stream, XINE_STREAM_INFO_VIDEO_WIDTH);
        xine->data_mine.file_info.height = xine_get_stream_info(
            xine->data_mine.stream, XINE_STREAM_INFO_VIDEO_HEIGHT);

        xine->data_mine.file_info.title = (char *)xine_get_meta_info(
            xine->data_mine.stream, XINE_META_INFO_TITLE);
        }

    return &(xine->data_mine.file_info);
}

char *djdxine_get_audio_lang(_Xine* xine,int channel)
{
    int rs;

    rs = xine_get_audio_lang(xine->data_mine.stream,channel,xine->lang);
    if (rs == 0)
        strcpy(xine->lang,"Unknown");
    return xine->lang;
}

char *djdxine_get_subtitle_lang(_Xine* xine,int channel)
{
    int rs;

    rs = xine_get_spu_lang(xine->data_mine.stream,channel,xine->lang);
    if (rs == 0)
        strcpy(xine->lang,"Unknown");
    return xine->lang;
}

char *djdxine_get_supported_extensions(_Xine* xine)
{
    return xine_get_file_extensions(xine->player.xine);
}

int djdxine_is_supported_input(_Xine* xine,const char *input)
{
    const char *const *input_plugins;
    const char* plugin;
    int rs;

    rs = 0;
    input_plugins = xine_list_input_plugins(xine->player.xine);

    plugin = *input_plugins++;
    while(plugin) {
        if (strcasecmp(plugin,input) == 0)
            rs = 1;
        plugin = *input_plugins++;
        }
    return rs;
}

char *djdxine_get_fatal_error(_Xine* xine)
{
    return xine->error;
}

char *djdxine_get_error(_Xine* xine)
{
    switch (xine_get_error(xine->player.stream)) {
        case XINE_ERROR_NONE:
            return "No error";
            break;
        case XINE_ERROR_NO_INPUT_PLUGIN:
            return "No input plugin to read this file";
            break;
        case XINE_ERROR_NO_DEMUX_PLUGIN:
            return "No demuxer plugin to read this file";
            break;
        case XINE_ERROR_DEMUX_FAILED:
            return "Demuxer failed to read this file";
            break;
        case XINE_ERROR_MALFORMED_MRL:
            return "Malformed MRL";
            break;
        case XINE_ERROR_INPUT_FAILED:
            return "Input failed to read this file";
            break;
        default:
            return "Unknown error";
            break;
    }
}
