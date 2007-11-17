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
        XINE_CONFIG_TYPE_STRING
        # xine param
        XINE_PARAM_SPU_CHANNEL
        XINE_PARAM_AUDIO_CHANNEL_LOGICAL
        XINE_PARAM_AUDIO_AMP_LEVEL


cdef extern from "djdxine.h":
    ctypedef struct _Xine
    ctypedef struct FileInfo:
        int width
        int height
        int duration
    enum djddummy:
        DJDXINE_STATUS_STOP
        DJDXINE_STATUS_PLAY
        DJDXINE_STATUS_PAUSE

    _Xine* djdxine_create(xine_event_listener_cb_t event_callback, void* event_callback_data)
    int djdxine_audio_init(_Xine* xine, char *audio_driver)
    int djdxine_video_init(_Xine* xine)
    int djdxine_attach(_Xine* xine, char *video_driver, char* display_name, int is_video)
    void djdxine_detach(_Xine* xine)
    void djdxine_destroy(_Xine* xine)
    void djdxine_load_config(_Xine* xine, char *filename)
    int djdxine_set_config_param(_Xine* xine, char *param_key, int type, void *value)
    int djdxine_play(_Xine* xine, char* filename, int isvideo,int fullscreen)
    void djdxine_stop(_Xine* xine)
    void djdxine_seek(_Xine* xine, int position)
    void djdxine_set_playing(_Xine* xine, int is_playing)
    int djdxine_get_status(_Xine* xine)
    void djdxine_set_param(_Xine* xine, int param, int value, int need_playing)
    int djdxine_get_parm(_Xine* xine, int param)
    int djdxine_get_position(_Xine* xine)
    int djdxine_set_fullscreen(_Xine* xine,int fullscreen)
    int djdxine_set_data_mine(_Xine* xine, char* filename)
    FileInfo* djdxine_file_info(_Xine* xine, char* filename)
    char *djdxine_get_audio_lang(_Xine* xine,int channel)
    char *djdxine_get_subtitle_lang(_Xine* xine,int channel)
    int djdxine_is_supported_input(_Xine* xine,char* input)
    char* djdxine_get_supported_extensions(_Xine* xine)
    char* djdxine_get_fatal_error(_Xine* xine)
    char* djdxine_get_error(_Xine* xine)


class NotPlayingError(Exception): pass
class FileInfoError(Exception): pass
class XineError(Exception): pass
class XineAlreadyAttached(Exception): pass

cdef class Xine:
    # Wrapper for the Xine class
    cdef _Xine* xine
    cdef object eos_callback
    cdef object progress_callback
    cdef int volume

    def __new__(self):
        self.xine = djdxine_create(onXineEvent,<void*>self)
        if self.xine == NULL:
            raise XineError("Unable to allocate memory")
        self.eos_callback = None
        self.progress_callback = None
        self.volume = 0
    def __dealloc__(self):
        if self.xine:
            djdxine_destroy(self.xine)
    def audio_init(self,char *audio_driver):
        if djdxine_audio_init(self.xine, audio_driver):
            err = djdxine_get_fatal_error(self.xine)
            raise XineError("XINE - " + err)
    def video_init(self):
        if djdxine_video_init(self.xine):
            err = djdxine_get_fatal_error(self.xine)
            raise XineError("XINE - " + err)
    def attach(self,char *video_driver,char *display,int is_video):
        rs=djdxine_attach(self.xine,video_driver,display,is_video)
        if rs == 1:
            err = djdxine_get_fatal_error(self.xine)
            raise XineError("XINE - " + err)
        elif rs == -1:
            raise XineAlreadyAttached()
        djdxine_set_param(self.xine, XINE_PARAM_AUDIO_AMP_LEVEL, self.volume, 0)
    def detach(self):
        djdxine_detach(self.xine)
    def load_config(self, char *filename):
        djdxine_load_config(self.xine,filename)
    def set_enum_config_param(self,char* key,int value):
        cdef int xine_type
        xine_type = XINE_CONFIG_TYPE_ENUM
        if djdxine_set_config_param(self.xine,key,xine_type,<void*>&value):
            raise XineError()
    def set_string_config_param(self,char* key,char *value):
        cdef int xine_type
        xine_type = XINE_CONFIG_TYPE_STRING
        if djdxine_set_config_param(self.xine,key,xine_type,<void*>value):
            raise XineError()
    def stop(self):
        djdxine_stop(self.xine)
    def start_playing(self,char* filename,int isvideo,int fullscreen):
        if djdxine_play(self.xine,filename,isvideo,fullscreen):
            raise XineError()
    def play(self):
        djdxine_set_playing(self.xine, 1)
    def pause(self):
        djdxine_set_playing(self.xine, 0)
    def get_status(self):
        status = djdxine_get_status(self.xine)
        if status == DJDXINE_STATUS_PLAY:
            return "play"
        elif status == DJDXINE_STATUS_PAUSE:
            return "pause"
        else:
            return "stop"
    def get_alang(self):
        return djdxine_get_parm(self.xine,XINE_PARAM_AUDIO_CHANNEL_LOGICAL)
    def get_slang(self):
        return djdxine_get_parm(self.xine,XINE_PARAM_SPU_CHANNEL)
    def set_alang(self, lang_idx):
        djdxine_set_param(self.xine, XINE_PARAM_AUDIO_CHANNEL_LOGICAL, lang_idx, 1)
    def set_slang(self, lang_idx):
        djdxine_set_param(self.xine, XINE_PARAM_SPU_CHANNEL, lang_idx, 1)
    def set_volume(self, volume):
        volume = min(max(volume, 0), 100)
        djdxine_set_param(self.xine, XINE_PARAM_AUDIO_AMP_LEVEL, volume, 0)
        self.volume = volume
    def get_volume(self):
        cdef int vol
        vol = djdxine_get_parm(self.xine,XINE_PARAM_AUDIO_AMP_LEVEL)
        if vol == -2: # stream not initialized
            return self.volume
        return vol
    def seek(self, int position):
        djdxine_seek(self.xine, position)
    def get_position(self):
        rs = djdxine_get_position(self.xine)
        if rs == -1:
            raise NotPlayingError()
        return rs
    def set_fullscreen(self, int fullscreen):
        if djdxine_set_fullscreen(self.xine,fullscreen):
            raise NotPlayingError()
    def get_file_info(self,char* filename):
        cdef FileInfo *file_info
        file_info = djdxine_file_info(self.xine,filename)
        if file_info == NULL:
            raise FileInfoError()
        return {"videowidth":file_info.width, "videoheight":file_info.height, "length":file_info.duration / 1000}
    def get_audio_lang(self,uri,channel):
        djdxine_set_data_mine(self.xine,uri)
        return djdxine_get_audio_lang(self.xine,channel)
    def get_subtitle_lang(self,uri,channel):
        djdxine_set_data_mine(self.xine,uri)
        return djdxine_get_subtitle_lang(self.xine,channel)
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
    def on_progress_event(self):
        if self.progress_callback:
            self.progress_callback()
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
