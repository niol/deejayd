/**************************************************************************
 * xine_impl.h
 **************************************************************************/

#include <pthread.h>
#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/keysym.h>
#include <X11/Xatom.h>
#include <X11/Xutil.h>
#include <X11/Xthreads.h>
#include <X11/extensions/XShm.h>
#define XINE_ENABLE_EXPERIMENTAL_FEATURES 1
#include <xine.h>

#define MWM_HINTS_DECORATIONS   (1L << 1)
#define PROP_MWM_HINTS_ELEMENTS 5

#define INPUT_MOTION (ExposureMask | KeyPressMask | \
                      StructureNotifyMask |        \
                      PropertyChangeMask)

typedef struct {
    uint32_t  flags;
    uint32_t  functions;
    uint32_t  decorations;
    int32_t   input_mode;
    uint32_t  status;
} MWMHints;

typedef struct {
    xmutex_rec* lock;
    int xpos;
    int ypos;
    int width;
    int height;
} FrameInfo;

typedef struct {
    int width;
    int height;
    int duration;
    char *title;
} FileInfo;

typedef struct {
    int playing;
    int isvideo;
    char *video_driver;
    char *audio_driver;
    xine_event_listener_cb_t event_callback;
    void* event_callback_data;
    FrameInfo frame_info;
    /* player */
    struct {
        Display* display;
        int screen;
        int fullscreen;
        Drawable window[2];
        double screen_pixel_aspect;
        pthread_t xevent_thread;

        xine_t* xine;
        xine_stream_t* stream;
        xine_video_port_t* vport;
        xine_audio_port_t* aport;
        xine_event_queue_t* event_queue;
        int video_init;
        } player;
    /* data mine to obtain file infos */
    struct {
        xine_t* xine;
        xine_stream_t* stream;
        xine_video_port_t* vport;
        xine_audio_port_t* aport;
        char *current_filename;
        FileInfo file_info;
        int init;
    } data_mine;
} _Xine;

/* Construct a Xine object */
_Xine* djdxine_init(const char *audio_driver,
                 xine_event_listener_cb_t event_callback,
                 void* event_callback_data);

int djdxine_set_config_param(_Xine* xine, const char *param_key, int type,
                              void *value);

/* Init video driver */
int djdxine_video_init(_Xine* xine, const char *video_driver,
                        const char* display_name); 

void djdxine_destroy(_Xine* xine);

int djdxine_play(_Xine* xine,const char* filename,int isvideo,int fullscreen);

void djdxine_stop(_Xine* xine);

void djdxine_seek(_Xine* xine, int position);

void djdxine_set_playing(_Xine* xine, int is_playing);

int djdxine_get_status(_Xine* xine);

void djdxine_set_volume(_Xine* xine, int volume);

int djdxine_get_volume(_Xine* xine);

int djdxine_get_position(_Xine* xine);

int djdxine_set_fullscreen(_Xine* xine,int fullscreen);

int djdxine_set_subtitle(_Xine* xine,int subtitle);

FileInfo* djdxine_file_info(_Xine* xine, const char* filename);

char* djdxine_get_supported_extensions(_Xine* xine);

int djdxine_is_supported_input(_Xine* xine,const char* input);

char* djdxine_get_error(_Xine* xine);
