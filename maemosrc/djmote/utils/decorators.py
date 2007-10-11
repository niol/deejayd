import gtk

# This is a decorator for our GUI callbacks : every GUI callback will be GTK
# thread safe that way.
def gui_callback(func):
    def gtk_thread_safe_func(*__args,**__kw):
        gtk.gdk.threads_enter()
        try:
            func(*__args, **__kw)
        finally:
            gtk.gdk.threads_leave()
    return gtk_thread_safe_func

# vim: ts=4 sw=4 expandtab
