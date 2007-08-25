import gtk
from djmote import stock

SIZE = gtk.icon_size_register("djmote-control", 16, 16)

class ControlButton(gtk.Button):

    def __init__(self):
        gtk.Button.__init__(self)
        self.set_focus_on_click(False)
        self.has_focus = False
        self.img = gtk.image_new_from_stock(self.__class__.stock_img,SIZE)
        self.set_image(self.img)


class PlayPauseButton(ControlButton):
    stock_img = stock.DJMOTE_PLAY

    def set_play(self, player_state):
        """Update the play/pause button to have the correct image."""
        if player_state == "play":
            stock_img = stock.DJMOTE_PAUSE
        else:
            stock_img = stock.DJMOTE_PLAY
        self.img.set_from_stock(stock_img,SIZE)
        self.set_image(self.img)


class NextButton(ControlButton):
    stock_img = stock.DJMOTE_NEXT


class PreviousButton(ControlButton):
    stock_img = stock.DJMOTE_PREVIOUS


class StopButton(ControlButton):
    stock_img = stock.DJMOTE_STOP

# FIXME : construct dict with introspection
buttons = {"play-pause":PlayPauseButton(), "stop":StopButton(), \
           "next":NextButton(),"previous":PreviousButton()}

# vim: ts=4 sw=4 expandtab
