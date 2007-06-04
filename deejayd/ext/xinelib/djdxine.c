/*************************************************************************
 * xine_impl.c
 **************************************************************************/

#include "Python.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "djdxine.h"
#include <xine/video_out.h>

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
    int xpos, ypos, width, height, border, depth;

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


/***************************************************************************
 *  Pubic functions
 *  ************************************************************************/

_Xine* djdxine_init(const char *audio_driver,
                xine_event_listener_cb_t event_callback,
                void* event_callback_data)
{
    _Xine* xine;

    xine = (_Xine*)malloc(sizeof(_Xine));
    if(xine == NULL) return NULL;
    xine->playing = 0;
    xine->isvideo = 0;
    xine->frame_info.lock = (xmutex_rec*)malloc(sizeof(xmutex_rec));
    xmutex_init(xine->frame_info.lock);
    xine->frame_info.xpos = 0;
    xine->frame_info.ypos = 0;
    xine->frame_info.width = 0;
    xine->frame_info.height = 0;
    xine->event_callback = event_callback;
    xine->event_callback_data = event_callback_data;
    xine->audio_driver = strdup(audio_driver);

    xine->video_driver = NULL;
    xine->player.video_init = 0;
    xine->data_mine.init = 0;

    /* create player */
    xine->player.xine = xine_new();
    xine_init(xine->player.xine);
    xine->player.aport = xine_open_audio_driver(xine->player.xine, 
                                                audio_driver, NULL);
    xine->player.vport = xine_open_video_driver(xine->player.xine, "none", 
                                            XINE_VISUAL_TYPE_NONE, NULL);
    xine->player.stream = xine_stream_new(xine->player.xine,xine->player.aport,
                                            xine->player.vport);

    xine->player.event_queue = xine_event_new_queue(xine->player.stream);
    xine_event_create_listener_thread(xine->player.event_queue,
        xine->event_callback,xine->event_callback_data);

    return xine;
}

int djdxine_set_config_param(_Xine* xine, const char *param_key, 
                                int type, void* value)
{
    xine_cfg_entry_t entry;

    if (!xine_config_lookup_entry (xine->player.xine, param_key, &entry))
        return 1;

    if (type == XINE_CONFIG_TYPE_ENUM) 
        entry.num_value = *(int *)value;
    else return 1;
    xine_config_update_entry(xine->player.xine,&entry);

    return 0;
}

int djdxine_video_init(_Xine* xine, const char *video_driver,
                        const char* display_name)
{
    double screen_width, screen_height;
    x11_visual_t vis;

    xine->video_driver = strdup(video_driver);
    if (!XInitThreads()) {
        return 1;
    }

    /* init video informations and player */
    xine->player.fullscreen = 0;
    xine->player.display = XOpenDisplay(display_name);
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

    /* close current stream to change video driver */
    xine_event_dispose_queue(xine->player.event_queue);
    xine_dispose(xine->player.stream);
    xine_close_video_driver(xine->player.xine, xine->player.vport);

    /* update video driver and create a new stream */
    vis.display = xine->player.display;
    vis.screen = xine->player.screen;
    vis.d = xine->player.window[xine->player.fullscreen];
    vis.dest_size_cb = dest_size_callback;
    vis.frame_output_cb = frame_output_callback;
    vis.user_data = xine;

    xine->player.vport = xine_open_video_driver(xine->player.xine, 
            xine->video_driver, XINE_VISUAL_TYPE_X11, (void *)&vis);
    xine->player.stream = xine_stream_new(xine->player.xine, 
        xine->player.aport,xine->player.vport);
    xine->player.event_queue = xine_event_new_queue(
                                                    xine->player.stream);
    xine_event_create_listener_thread(xine->player.event_queue,
        xine->event_callback,xine->event_callback_data);
    xine->player.video_init = 1;

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
    xine->data_mine.init = 1;

    return 0;
}

void djdxine_destroy(_Xine* xine)
{
    free(xine->audio_driver);
    if (xine->video_driver) free(xine->video_driver);

    if (xine->playing) {
        djdxine_stop(xine);
        }

    /* close data mine */
    if (xine->data_mine.init) {
        if (xine->data_mine.current_filename) {
            free (xine->data_mine.current_filename);
            xine_close(xine->data_mine.stream);
        }
        xine_dispose(xine->data_mine.stream);
        xine_close_audio_driver(xine->data_mine.xine, xine->data_mine.aport);
        xine_close_video_driver(xine->data_mine.xine, xine->data_mine.vport);
        xine_exit(xine->data_mine.xine);
    }

    /* close player */
    xine_event_dispose_queue(xine->player.event_queue);
    xine_dispose(xine->player.stream);
    xine_close_audio_driver(xine->player.xine, xine->player.aport);
    xine_close_video_driver(xine->player.xine, xine->player.vport);
    xine_exit(xine->player.xine);

    /* close video parm */
    if (xine->player.video_init) {
        _destroy_windows(xine);
        XCloseDisplay(xine->player.display);
    }

    xmutex_clear(xine->frame_info.lock);
    free(xine);
}

int djdxine_play(_Xine* xine, const char* filename, int isvideo, int fullscreen)
{
    if (xine->playing) {
        djdxine_stop(xine);
    }

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

    xine->isvideo = isvideo;
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
        xine->isvideo = 0;
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

void djdxine_set_volume(_Xine* xine, int volume)
{
    xine_set_param(xine->player.stream, XINE_PARAM_AUDIO_AMP_LEVEL, volume);
}

int djdxine_get_volume(_Xine* xine)
{
    return xine_get_param(xine->player.stream, XINE_PARAM_AUDIO_AMP_LEVEL);
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

int djdxine_set_subtitle(_Xine* xine,int subtitle)
{
    if ((!xine->playing) || (!xine->isvideo)) return 1;

    xine_set_param(xine->player.stream,XINE_PARAM_IGNORE_SPU,!subtitle);
    return 0;
}

int _set_data_mine(_Xine* xine, const char* filename)
{
  int rv;
  if (xine->data_mine.current_filename) {
    if (!strcmp (filename, xine->data_mine.current_filename)) {
      return 2;
    }
    xine_close(xine->data_mine.stream);
    free (xine->data_mine.current_filename);
    free (xine->data_mine.file_info.title);
  }
  rv = xine_open(xine->data_mine.stream, filename);
  if (rv) {
    xine->data_mine.current_filename = strdup (filename);
  }
  return rv;
}

FileInfo *djdxine_file_info(_Xine* xine, const char* filename)
{
    int rv;
    int duration;
    int dummy, dummy2;
    rv = _set_data_mine(xine, filename);
    if (rv == 0)
        return NULL;
    if (rv == 1)
        xine_get_pos_length(xine->data_mine.stream,&dummy, &dummy2, &duration);
        xine->data_mine.file_info.duration = duration;
        xine->data_mine.file_info.width = xine_get_stream_info(
            xine->data_mine.stream, XINE_STREAM_INFO_VIDEO_WIDTH);
        xine->data_mine.file_info.height = xine_get_stream_info(
            xine->data_mine.stream, XINE_STREAM_INFO_VIDEO_HEIGHT);

        xine->data_mine.file_info.title = xine_get_meta_info(
            xine->data_mine.stream, XINE_META_INFO_TITLE);

    return &(xine->data_mine.file_info);
}

char *djdxine_get_supported_mimetypes(_Xine* xine)
{
    return xine_get_mime_types(xine->player.xine);
}

char *djdxine_get_supported_extensions(_Xine* xine)
{
    return xine_get_file_extensions(xine->player.xine);
}

char *djdxine_get_error(_Xine* xine)
{
    switch (xine_get_error(xine->player.stream)) {
        case XINE_ERROR_NONE:
            return "No error";
            break;
        case XINE_ERROR_NO_INPUT_PLUGIN:
            return "No imput plugin to read this file";
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

/****************************************************************************
 ****************************************************************************
static int Y_table[256];
static int RCr_table[256];
static int GCr_table[256];
static int GCb_table[256];
static int BCb_table[256];
static int tables_initialized = 0;

static unsigned char normalize(int val) {
  if (val < 0)
    val = 0;
  if (val > (255 << 8))
    val = 255 << 8;
  val = val + 127;
  val = val >> 8;
  return val;
}

static void build_tables() {
  int i;
  if (tables_initialized)
    return;
  for (i = 0; i < 256; i++) {
    Y_table[i] = (i - 16) * 255 * 256 / 219;
    RCr_table[i] = (i - 128) * 127 * 256 * 1.402 / 112;
    GCr_table[i] = (i - 128) * 127 * 256 * -.714 / 112;
    GCb_table[i] = (i - 128) * 127 * 256 * -.344 / 112;
    BCb_table[i] = (i - 128) * 127 * 256 * 1.772 / 112;
  }
  tables_initialized = 1;
}

int xineFileScreenshot(_Xine *xine, const char* filename, const char *screenshot)
{
    int rv;
    int duration;
    xine_video_frame_t frame;
    int i, j;
    int CbOffset;
    int CrOffset;
    unsigned char *out_data;
    GdkPixbuf *pixbuf;
    xine_video_port_t *video_out;

    rv = xineDataMineFilename(xine, filename);
    if (rv == 0)
      return 1;
    duration = xineFileDuration(xine, filename);
    if(duration == -1)
      return 1;
    if (!xine_get_stream_info (xine->data_mine.stream, XINE_STREAM_INFO_HAS_VIDEO))
      return 1;
    rv = xine_play(xine->data_mine.stream, 0, duration / 2);
    if (rv == 0)
      return 1;
    video_out = xine->data_mine.videoPort;
    if (video_out->get_property (video_out, VO_PROP_NUM_STREAMS) == 0) {
        return 1;
    }
    rv = xine_get_next_video_frame (video_out, &frame);
    if (rv == 0)
      return 1;
    if (frame.colorspace != XINE_IMGFMT_YV12 &&
	frame.colorspace != XINE_IMGFMT_YUY2) {
      xine_free_video_frame (video_out, &frame);
      return 0;
    }
    build_tables();
    out_data = malloc (frame.width * frame.height * 3);
    switch (frame.colorspace) {
    case XINE_IMGFMT_YV12:
      CrOffset = frame.width * frame.height;
      CbOffset = frame.width * frame.height + (frame.width / 2) * (frame.height / 2);
      for (j = 0; j < frame.height; j++) {
	for (i = 0; i < frame.width; i++) {
	  int pixel = j * frame.width + i;
	  int subpixel = (j / 2) * (frame.width / 2) + (i / 2);
	  int Y = Y_table[frame.data[pixel]];
	  out_data[pixel * 3] =
	    normalize(Y +
		      RCr_table[frame.data[CrOffset + subpixel]]);
	  out_data[pixel * 3 + 1] =
	    normalize(Y +
		      GCr_table[frame.data[CrOffset + subpixel]] +
		      GCb_table[frame.data[CbOffset + subpixel]]);
	  out_data[pixel * 3 + 2] =
	    normalize(Y +
		      BCb_table[frame.data[CbOffset + subpixel]]);
	}
      }
      break;

    case XINE_IMGFMT_YUY2:
      CrOffset = 3;
      CbOffset = 1;
      for (j = 0; j < frame.height; j++) {
	for (i = 0; i < frame.width; i++) {
	  int pixel = j * frame.width + i;
	  int subpixel = (j * frame.width + i) / 2 * 4;
	  int Y = Y_table[frame.data[pixel * 2]];
	  out_data[pixel * 3] =
	    normalize(Y +
		      RCr_table[frame.data[CrOffset + subpixel]]);
	  out_data[pixel * 3 + 1] =
	    normalize(Y +
		      GCr_table[frame.data[CrOffset + subpixel]] +
		      GCb_table[frame.data[CbOffset + subpixel]]);
	  out_data[pixel * 3 + 2] =
	    normalize(Y +
		      BCb_table[frame.data[CbOffset + subpixel]]);
	}
      }
      break;
    }
    pixbuf = gdk_pixbuf_new_from_data (out_data, GDK_COLORSPACE_RGB, 0,
				       8, frame.width, frame.height, frame.width * 3,
				       NULL, NULL);
    gdk_pixbuf_save (pixbuf, screenshot, "png", NULL, NULL);
    gdk_pixbuf_unref (pixbuf);
    free (out_data);
    xine_free_video_frame (xine->data_mine.videoPort, &frame);
    return 1;
}
*/
