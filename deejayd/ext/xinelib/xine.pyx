##############################################################################
# Xine module.  
#
# Contains the Xine class which is used to control libxine.
# Code in here is basically just a wrapper for the functions in djdxine.c.
# See that file if you want to know what's going on under the hood
#
##############################################################################

cdef extern from "X11/Xlib.h":
    ctypedef unsigned long Drawable

cdef extern from "Python.h":
    ctypedef int PyGILState_STATE
    PyGILState_STATE PyGILState_Ensure()
    void PyGILState_Release(PyGILState_STATE)
    ctypedef struct PyThreadState
    ctypedef struct PyObject
    void Py_DECREF(PyObject*)
    void Py_INCREF(PyObject*)
    PyObject* PyObject_CallMethod(PyObject *o, char *method, char* format, ...)
    void PyErr_Print()

cdef extern from "xine.h":
    ctypedef struct xine_event_t:
        int type
        void* data
    ctypedef struct xine_progress_data_t:
        int percent
        char* description
    ctypedef void (*xine_event_listener_cb_t) (void *user_data,
            xine_event_t *event)
    enum dummy:
        # xine event
        XINE_EVENT_UI_PLAYBACK_FINISHED
        XINE_EVENT_PROGRESS
        # config entry data types
        XINE_CONFIG_TYPE_ENUM
        # Xine status
        XINE_STATUS_IDLE
        XINE_STATUS_STOP
        XINE_STATUS_PLAY
        XINE_STATUS_QUIT


cdef extern from "djdxine.h":
    ctypedef struct _Xine
    ctypedef struct FileInfo:
        int width
        int height
        int duration

    _Xine* djdxine_init(char *audio_driver, xine_event_listener_cb_t event_callback,void* event_callback_data) 
    int djdxine_set_config_param(_Xine* xine, char *param_key, int type, void *value)
    int djdxine_video_init(_Xine* xine, char *video_driver,char* display_name)
    void djdxine_destroy(_Xine* xine)
    int djdxine_play(_Xine* xine, char* filename, int isvideo,int fullscreen)
    void djdxine_stop(_Xine* xine)
    void djdxine_seek(_Xine* xine, int position)
    void djdxine_set_playing(_Xine* xine, int is_playing)
    int djdxine_get_status(_Xine* xine)
    void djdxine_set_volume(_Xine* xine, int volume)
    int djdxine_get_volume(_Xine* xine)
    int djdxine_get_position(_Xine* xine)
    int djdxine_set_fullscreen(_Xine* xine,int fullscreen)
    int djdxine_set_subtitle(_Xine* xine,int subtitle)
    FileInfo* djdxine_file_info(_Xine* xine, char* filename)
    int djdxine_is_supported_input(_Xine* xine,char* input)
    char* djdxine_get_supported_extensions(_Xine* xine)
    char* djdxine_get_error(_Xine* xine)


class NotPlayingError(Exception): pass
class FileInfoError(Exception): pass
class XineError(Exception): pass

cdef class Xine:
    # Wrapper for the Xine class
    cdef _Xine* xine
    cdef object eos_callback
    cdef object progress_callback

    def __new__(self,char *audio_driver):
        self.xine = djdxine_init(audio_driver,onXineEvent,<void*>self)
        self.eos_callback = None
        self.progress_callback = None
    def __dealloc__(self):
        djdxine_destroy(self.xine)
    def set_enum_config_param(self,char* key,int value):
        cdef int xine_type
        xine_type = XINE_CONFIG_TYPE_ENUM
        if djdxine_set_config_param(self.xine,key,xine_type,<void*>&value):
            raise XineError
    def video_init(self,char *video_driver,char* display_name):
        djdxine_video_init(self.xine,video_driver,display_name)
    def stop(self):
        djdxine_stop(self.xine)
    def start_playing(self,char* filename,int isvideo,int fullscreen):
        if djdxine_play(self.xine,filename,isvideo,fullscreen):
            raise XineError
    def play(self):
        djdxine_set_playing(self.xine, 1)
    def pause(self):
        djdxine_set_playing(self.xine, 0)
    def get_status(self):
        status = djdxine_get_status(self.xine)
        if status == XINE_STATUS_PLAY:
            return "play"
        else:
            return "stop"
    def set_volume(self, volume):
        volume = min(max(volume, 0), 100)
        djdxine_set_volume(self.xine, volume)
    def get_volume(self):
        return djdxine_get_volume(self.xine)
    def seek(self, int position):
        djdxine_seek(self.xine, position)
    def get_position(self):
        rs = djdxine_get_position(self.xine)
        if rs == -1:
            raise NotPlayingError
        return rs
    def set_fullscreen(self, int fullscreen):
        if djdxine_set_fullscreen(self.xine,fullscreen):
            raise NotPlayingError
    def set_subtitle(self, int subtitle):
        if djdxine_set_subtitle(self.xine,subtitle):
            raise NotPlayingError
    def get_file_info(self,char* filename):
        cdef FileInfo *file_info
        file_info = djdxine_file_info(self.xine,filename)
        if file_info == NULL:
            raise FileInfoError 
        return {"videowidth":file_info.width, "videoheight":file_info.height, "length":file_info.duration / 1000}
    def is_supported_input(self,char* input):
        return djdxine_is_supported_input(self.xine,input)
    def get_supported_extensions(self):
        return djdxine_get_supported_extensions(self.xine)
    def set_eos_callback(self, callback):
        self.eos_callback = callback
    def set_progress_callback(self, callback):
        self.progress_callback = callback
    def on_eos_event(self):
        if self.eos_callback:
            self.eos_callback()
    def on_progress_event(self,percent,description):
        if self.progress_callback:
            self.progress_callback(description,percent)
    def get_error(self):
        return djdxine_get_error(self.xine)

cdef void onXineEvent(void* data, xine_event_t* event):
    cdef PyObject* self
    cdef PyGILState_STATE gil
    cdef PyObject* result
    cdef xine_progress_data_t* pevent

    if event.type == XINE_EVENT_UI_PLAYBACK_FINISHED:
        self = <PyObject*>data
        gil = PyGILState_Ensure()
        Py_INCREF(self)
        result = PyObject_CallMethod(self, "on_eos_event", "", NULL)
        if(result == NULL):
            PyErr_Print()
        else:
            Py_DECREF(result)
        Py_DECREF(self)
        PyGILState_Release(gil)
    elif event.type == XINE_EVENT_PROGRESS:
        pevent = <xine_progress_data_t*>event.data
        self = <PyObject*>data
        gil = PyGILState_Ensure()
        Py_INCREF(self)
        result = PyObject_CallMethod(self, "on_progress_event", "(is)", pevent.percent,pevent.description)
        if(result == NULL):
            PyErr_Print()
        else:
            Py_DECREF(result)
        Py_DECREF(self)
        PyGILState_Release(gil)
