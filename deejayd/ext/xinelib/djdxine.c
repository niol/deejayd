/*************************************************************************
 * xine_impl.c
 **************************************************************************/

#include "Python.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "djdxine.h"
#include <xine/video_out.h>

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
    *dest_pixel_aspect = xine->video_player.screen_pixel_aspect;
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
    *dest_pixel_aspect = xine->video_player.screen_pixel_aspect;
}

static void _set_video_area(_Xine* xine)
{
    Window root;
    int xpos, ypos, width, height, border, depth;

    XGetGeometry(xine->video_player.display,
        xine->video_player.window[xine->video_player.fullscreen],
        &root,&xpos,&ypos,&width,&height,&border,&depth);
    xmutex_lock(xine->frame_info.lock);
    xine->frame_info.xpos = xpos;
    xine->frame_info.ypos = ypos;
    xine->frame_info.width = width;
    xine->frame_info.height = height;
    xmutex_unlock(xine->frame_info.lock);
}

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
    xine->video_player.init = 0;
    xine->data_mine.init = 0;

    /* create an audio player */
    xine->audio_player.xine = xine_new();
    xine_init(xine->audio_player.xine);
    xine->audio_player.aport = xine_open_audio_driver(xine->audio_player.xine,
            xine->audio_driver, NULL);
    xine->audio_player.vport = xine_open_video_driver(xine->audio_player.xine, 
            "none", XINE_VISUAL_TYPE_NONE, NULL);
    xine->audio_player.stream = xine_stream_new(xine->audio_player.xine, 
        xine->audio_player.aport,xine->audio_player.vport);
    xine->audio_player.event_queue = xine_event_new_queue(
                                                    xine->audio_player.stream);
    xine_event_create_listener_thread(xine->audio_player.event_queue,
        xine->event_callback,xine->event_callback_data);

    return xine;
}

int djdxine_video_init(_Xine* xine, const char *video_driver,
                        const char* display_name)
{
    double screen_width, screen_height;

    xine->video_driver = strdup(video_driver);
    if (!XInitThreads()) {
        return 1;
    }

    /* init video informations and player */
    xine->video_player.fullscreen = 0;
    xine->video_player.display = XOpenDisplay(display_name);
    xine->video_player.screen = XDefaultScreen(xine->video_player.display);
    screen_width = (DisplayWidth(xine->video_player.display, 
        xine->video_player.screen) * 1000 / DisplayWidthMM(
        xine->video_player.display, xine->video_player.screen));
    screen_height = (DisplayHeight(xine->video_player.display, 
        xine->video_player.screen) * 1000 / DisplayHeightMM(
        xine->video_player.display, xine->video_player.screen));
    xine->video_player.screen_pixel_aspect = screen_height / screen_width;
    
    xine->video_player.xine = xine_new();
    xine_init(xine->video_player.xine);
    xine->video_player.aport = xine_open_audio_driver(xine->video_player.xine,
            xine->audio_driver, NULL);

    xine->video_player.init = 1;

    /* Create a xine instance used for querying data about video files */
    xine->data_mine.xine = xine_new();
    xine_init(xine->data_mine.xine);
    xine->data_mine.video_port = xine_new_framegrab_video_port(
        xine->data_mine.xine);
    xine->data_mine.audio_port = xine_open_audio_driver(xine->data_mine.xine, 
        "none", NULL);
    xine->data_mine.stream = xine_stream_new(xine->data_mine.xine,
            xine->data_mine.audio_port, xine->data_mine.video_port);
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
        xine_close_audio_driver(xine->data_mine.xine, 
                                        xine->data_mine.audio_port);
        xine_close_video_driver(xine->data_mine.xine, 
                                        xine->data_mine.video_port);
        xine_exit(xine->data_mine.xine);
    }

    /* close video player */
    if (xine->video_player.init) {
        xine_close_audio_driver(xine->video_player.xine, 
                                        xine->video_player.aport);
        xine_exit(xine->video_player.xine);
        XCloseDisplay(xine->video_player.display);
    }

    /* close audio player */
    xine_event_dispose_queue(xine->audio_player.event_queue);
    xine_dispose(xine->audio_player.stream);
    xine_close_audio_driver(xine->audio_player.xine, xine->audio_player.aport);
    xine_close_video_driver(xine->audio_player.xine, xine->audio_player.vport);
    xine_exit(xine->audio_player.xine);
    xmutex_clear(xine->frame_info.lock);
    free(xine);
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

static void _create_video_player(_Xine* xine)
{
    int xpos, ypos, width, height;
    MWMHints mwmhints;
    Atom XA_NO_BORDER;
    x11_visual_t vis;

    XLockDisplay(xine->video_player.display);
    XA_NO_BORDER = XInternAtom(xine->video_player.display, 
                "_MOTIF_WM_HINTS", False);
    mwmhints.flags = MWM_HINTS_DECORATIONS;
    mwmhints.decorations = 0;

    /* create fullscreen window*/
    xine->video_player.window[1] = XCreateSimpleWindow(
        xine->video_player.display, 
        XDefaultRootWindow(xine->video_player.display),0, 0, 
        (DisplayWidth(xine->video_player.display, 
        xine->video_player.screen)), (DisplayHeight(
        xine->video_player.display, xine->video_player.screen)), 0, 0, 0);
    XSelectInput(xine->video_player.display, xine->video_player.window[1], 
                    INPUT_MOTION);
    XChangeProperty(xine->video_player.display, 
        xine->video_player.window[1],XA_NO_BORDER, 
        XA_NO_BORDER, 32, PropModeReplace, 
        (unsigned char *) &mwmhints,PROP_MWM_HINTS_ELEMENTS);
    /* hide cursor */
    _hide_cursor(xine->video_player.display,xine->video_player.window[1]);

    /* create normal window */
    xpos    = 0;
    ypos    = 0;
    width   = 640;
    height  = 400;
    xine->video_player.window[0] = XCreateSimpleWindow(
        xine->video_player.display, 
        XDefaultRootWindow(xine->video_player.display),
        xpos,ypos,width,height,1,0,0);
    XSelectInput(xine->video_player.display, xine->video_player.window[0], 
                    INPUT_MOTION);

    XMapRaised(xine->video_player.display, 
        xine->video_player.window[xine->video_player.fullscreen]);
    XSync(xine->video_player.display, False);
    XUnlockDisplay(xine->video_player.display);

    vis.display = xine->video_player.display;
    vis.screen = xine->video_player.screen;
    vis.d = xine->video_player.window[xine->video_player.fullscreen];
    vis.dest_size_cb = dest_size_callback;
    vis.frame_output_cb = frame_output_callback;
    vis.user_data = xine;

    _set_video_area(xine);
    xine->video_player.vport = xine_open_video_driver(xine->video_player.xine, 
            xine->video_driver, XINE_VISUAL_TYPE_X11, (void *)&vis);

    xine->video_player.stream = xine_stream_new(xine->video_player.xine, 
        xine->video_player.aport,xine->video_player.vport);
    xine->video_player.event_queue = xine_event_new_queue(
                                                    xine->video_player.stream);
    xine_event_create_listener_thread(xine->video_player.event_queue,
        xine->event_callback,xine->event_callback_data);

    xine_port_send_gui_data(xine->video_player.vport, 
            XINE_GUI_SEND_DRAWABLE_CHANGED,
            (void *) xine->video_player.window[xine->video_player.fullscreen]);
    xine_port_send_gui_data(xine->video_player.vport, 
            XINE_GUI_SEND_VIDEOWIN_VISIBLE,(void *) 1);
}

static void _destroy_video_player(_Xine* xine)
{
        xine_event_dispose_queue(xine->video_player.event_queue);
        xine_dispose(xine->video_player.stream);

        xine_close_video_driver(xine->video_player.xine, 
                                        xine->video_player.vport);
}

int djdxine_set_fullscreen(_Xine* xine,int fullscreen)
{
    if ((!xine->playing) || (!xine->isvideo)) return 1;
    if (xine->video_player.fullscreen == fullscreen) return 0;

    XLockDisplay(xine->video_player.display);
    XUnmapWindow(xine->video_player.display, 
                 xine->video_player.window[xine->video_player.fullscreen]);
    XMapRaised(xine->video_player.display, 
               xine->video_player.window[fullscreen]);
    XSync(xine->video_player.display, False);
    XUnlockDisplay(xine->video_player.display);

    xine->video_player.fullscreen = fullscreen;
    xine_port_send_gui_data(xine->video_player.vport, 
        XINE_GUI_SEND_DRAWABLE_CHANGED,
        (void*) xine->video_player.window[fullscreen]);
    _set_video_area(xine);

    return 0;
}

int djdxine_play(_Xine* xine, const char* filename, int isvideo)
{
    if (xine->playing) {
        djdxine_stop(xine);
    }

    if (isvideo) {
        _create_video_player(xine);
        if (!xine_open(xine->video_player.stream, filename) || 
                               !xine_play(xine->video_player.stream, 0, 0)) {
            return 1;
            }
    }
    else {
        if (!xine_open(xine->audio_player.stream, filename) || 
                               !xine_play(xine->audio_player.stream, 0, 0)) {
            return 1;
            }
        }

    xine->isvideo = isvideo;
    xine->playing = 1;
    return 0;
}

int djdxine_next(_Xine* xine, const char* filename, int isvideo)
{
    if (isvideo) {
        if (xine->isvideo) { xine_close(xine->video_player.stream);}
        else { xine_close(xine->audio_player.stream); }
        if (!xine_open(xine->video_player.stream, filename) || 
                               !xine_play(xine->video_player.stream, 0, 0)) {
            return 1;
            }
    }
    else {
        if (xine->isvideo) {djdxine_stop(xine); }
        else { xine_close(xine->audio_player.stream); }
        if (!xine_open(xine->audio_player.stream, filename) || 
                               !xine_play(xine->audio_player.stream, 0, 0)) {
            return 1;
            }
    }

    xine->isvideo = isvideo;
    xine->playing = 1;
    return 0;
}

void djdxine_stop(_Xine* xine)
{
    if(!xine->playing) return;

    if (xine->isvideo) {
        xine_close(xine->video_player.stream);
        _destroy_video_player(xine);

        XLockDisplay(xine->video_player.display);
        XUnmapWindow(xine->video_player.display, 
                     xine->video_player.window[xine->video_player.fullscreen]);
        XDestroyWindow(xine->video_player.display, 
                       xine->video_player.window[0]);
        XDestroyWindow(xine->video_player.display, 
                       xine->video_player.window[1]);
        XUnlockDisplay(xine->video_player.display);
        xine->isvideo = 0;
    }
    else {xine_close(xine->audio_player.stream);}

    xine->playing = 0;
}

int djdxine_set_data_mine(_Xine* xine, const char* filename)
{
  int rv;
  if (xine->data_mine.current_filename) {
    if (!strcmp (filename, xine->data_mine.current_filename)) {
      return 1;
    }
    xine_close(xine->data_mine.stream);
    free (xine->data_mine.current_filename);
  }
  rv = xine_open(xine->data_mine.stream, filename);
  if (rv) {
    xine->data_mine.current_filename = strdup (filename);
  }
  return rv;
}

int djdxine_file_info(_Xine* xine, const char* filename)
{
    int rv;
    int duration;
    int dummy, dummy2;
    rv = djdxine_set_data_mine(xine, filename);
    if (rv == 0)
      return -1;
    if (rv == 0)
      return -1;
    return duration;
}

void djdxine_seek(_Xine* xine, int position)
{
    if(!xine->playing) return;
    if (xine->isvideo) xine_play(xine->video_player.stream, 0, position);
    else xine_play(xine->audio_player.stream, 0, position);
}

void djdxine_set_playing(_Xine* xine, int is_playing)
{
    xine_stream_t* stream;
    if(!xine->playing) return;

    if (xine->isvideo) stream = xine->video_player.stream;
    else stream = xine->audio_player.stream;

    if(is_playing) {
        xine_set_param(stream, XINE_PARAM_SPEED, XINE_SPEED_NORMAL);
    } else {
        xine_set_param(stream, XINE_PARAM_SPEED, XINE_SPEED_PAUSE);
    }
}

int djdxine_set_volume(_Xine* xine, int volume)
{
    xine_stream_t* stream;
    if(!xine->playing) return 1;

    if (xine->isvideo) stream = xine->video_player.stream;
    else stream = xine->audio_player.stream;

    xine_set_param(stream, XINE_PARAM_AUDIO_AMP_LEVEL, volume);
    return 0;
}

int djdxine_get_volume(_Xine* xine)
{
    xine_stream_t* stream;
    if(!xine->playing) return -1;

    if (xine->isvideo) stream = xine->video_player.stream;
    else stream = xine->audio_player.stream;

    return xine_get_param(stream, XINE_PARAM_AUDIO_AMP_LEVEL);
}

void djdxine_got_expose_event(_Xine* xine, int x, int y, int width, int height)
{
    XExposeEvent expose;

    if(!xine->playing) return;
    /* set as much of the XExposeEvent as we can.  Some fields like serial
     * won't be filled in, but this doesn't cause problems in practice.  Totem
     * doesn't fill in anything, so our method can't be too bad. */
    memset(&expose, 0, sizeof(XExposeEvent));
    expose.x = x;
    expose.y = y;
    expose.width = width;
    expose.height = height;
    expose.display = xine->video_player.display;
    expose.window = xine->video_player.window[0];
    xine_port_send_gui_data(xine->video_player.vport, 
            XINE_GUI_SEND_EXPOSE_EVENT, &expose);
}

void djdxine_set_area(_Xine* xine, int xpos, int ypos, int width, int height)
{
    xmutex_lock(xine->frame_info.lock);
    xine->frame_info.xpos = xpos;
    xine->frame_info.ypos = ypos;
    xine->frame_info.width = width;
    xine->frame_info.height = height;
    xmutex_unlock(xine->frame_info.lock);
}

void djdxine_set_error(_Xine* xine,char *error)
{
}

char *djd_get_error(_Xine* xine)
{
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
