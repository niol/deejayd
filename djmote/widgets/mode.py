import gtk
from djmote.widgets.playlist import PlaylistBox

class ModeBox(gtk.VBox):

    def __init__(self,player):
        gtk.VBox.__init__(self)
        self.__player = player
        self.__content = None

    def update_status(self, status):
        if not self.__content:
            self.__build(status)
        self.__content["widget"].update_status(status)

    def post_show_action(self):
        pass

    def __build(self,status):
        if status["mode"] == "playlist":
            box = PlaylistBox(self.__player)
            box.update_status(status)
        self.__content = {"name": status["mode"],"widget": box}
        self.pack_start(self.__content["widget"])
        self.show_all()


# vim: ts=4 sw=4 expandtab
