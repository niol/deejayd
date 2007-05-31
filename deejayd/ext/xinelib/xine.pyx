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
        XINE_EVENT_UI_PLAYBACK_FINISHED
        XINE_EVENT_PROGRESS

cdef extern from "djdxine.h":
    ctypedef struct _Xine
    ctypedef struct FileInfo:
        int width
        int height
        int duration

    _Xine* djdxine_init(char *audio_driver, xine_event_listener_cb_t event_callback,void* event_callback_data) 
    int djdxine_video_init(_Xine* xine, char *video_driver,char* display_name)
    void djdxine_destroy(_Xine* xine)
    int djdxine_play(_Xine* xine, char* filename, int isvideo)
    void djdxine_stop(_Xine* xine)
    void djdxine_seek(_Xine* xine, int position)
    void djdxine_set_playing(_Xine* xine, int is_playing)
    void djdxine_set_volume(_Xine* xine, int volume)
    int djdxine_get_volume(_Xine* xine)
    int djdxine_get_position(_Xine* xine)
    int djdxine_set_fullscreen(_Xine* xine,int fullscreen)
    FileInfo* djdxine_file_info(_Xine* xine, char* filename)
    char* djdxine_get_supported_mimetypes(_Xine* xine)
    char* djdxine_get_supported_extensions(_Xine* xine)


class NotPlayingError(Exception): pass
class StartPlayingError(Exception): pass
class FileInfoError(Exception): pass

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
    def video_init(self,char *video_driver,char* display_name):
        djdxine_video_init(self.xine,video_driver,display_name)
    def stop(self):
        djdxine_stop(self.xine)
    def start_playing(self,char* filename,int isvideo):
        if djdxine_play(self.xine,filename,isvideo):
            raise StartPlayingError
    def play(self):
        djdxine_set_playing(self.xine, 1)
    def pause(self):
        djdxine_set_playing(self.xine, 0)
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
    def get_file_info(self,char* filename):
        cdef FileInfo *file_info
        file_info = djdxine_file_info(self.xine,filename)
        if file_info == NULL:
            raise FileInfoError 
        return {"videowidth":file_info.width, "videoheight":file_info.height, "length":file_info.duration}
    def get_supported_mimetypes(self):
        return djdxine_get_supported_mimetypes(self.xine)
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
