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
    ctypedef void (*xine_event_listener_cb_t) (void *user_data,
            xine_event_t *event)
    enum dummy:
        XINE_EVENT_UI_PLAYBACK_FINISHED

cdef extern from "djdxine.h":
    ctypedef struct _Xine

    _Xine* djdxine_init(char *audio_driver, xine_event_listener_cb_t event_callback,void* event_callback_data) 
    int djdxine_video_init(_Xine* xine, char *video_driver,char* display_name)
    void djdxine_destroy(_Xine* xine)
    int djdxine_play(_Xine* xine, char* filename, int isvideo)
    void djdxine_stop(_Xine* xine)
    int djdxine_file_info(_Xine* xine, char* filename)
    void djdxine_seek(_Xine* xine, int position)
    void djdxine_set_playing(_Xine* xine, int is_playing)
    int djdxine_set_volume(_Xine* xine, int volume)
    int djdxine_get_volume(_Xine* xine)
    int djdxine_get_pos_length(_Xine* xine, int* position, int* length)
    int djdxine_set_fullscreen(_Xine* xine,int fullscreen)
    void djdxine_got_expose_event(_Xine* xine, int x, int y, int width, int height)
    void djdxine_set_area(_Xine* xine, int xpos, int ypos, int width, int height)


class NotPlayingError(Exception): pass
class StartPlayingError(Exception): pass

cdef class Xine:
    # Wrapper for the Xine class
    cdef _Xine* xine
    cdef object eos_callback

    def __new__(self,char *audio_driver):
        self.xine = djdxine_init(audio_driver,onXineEvent,<void*>self)
        self.eos_callback = None
    def __dealloc__(self):
        djdxine_destroy(self.xine)
    def video_init(self,char *video_driver,char* display_name):
        djdxine_video_init(self.xine,video_driver,display_name)
    def stop(self):
        djdxine_stop(self.xine)
    def start_playing(self,char* filename,int isvideo):
        if djdxine_play(self.xine,filename,isvideo):
            raise startplayingerror
    def play(self):
        djdxine_set_playing(self.xine, 1)
    def pause(self):
        djdxine_set_playing(self.xine, 0)
    def set_volume(self, volume):
        volume = min(max(volume, 0), 100)
        if djdxine_set_volume(self.xine, volume):
            raise NotPlayingError
    def get_volume(self):
        rs = djdxine_get_volume(self.xine)
        if rs == -1:
            raise NotPlayingError
        return rs
    def seek(self, int position):
        djdxine_seek(self.xine, position)
    def set_fullscreen(self, int fullscreen):
        if djdxine_set_fullscreen(self.xine,fullscreen):
            raise NotPlayingError
    def set_eos_callback(self, callback):
        self.eos_callback = callback
    def on_eos_event(self):
        if self.eos_callback:
            self.eos_callback()

cdef void onXineEvent(void* data, xine_event_t* event):
    cdef PyObject* self
    cdef PyGILState_STATE gil
    cdef PyObject* result

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
