import gtk,hildon
from djmote import stock

class ControlBox(gtk.VBox):

    def __init__(self,player):
        gtk.VBox.__init__(self)

        vol_button = VolumeButton(True)
        vol_button.connect("clicked",self.volume_toggle)
        self.pack_end(vol_button)

        self.__current = "pl_controls"
        self.__controls_panels = {}

        self.__controls_panels["pl_controls"] = ControlsPanel(player)
        self.pack_end(self.__controls_panels["pl_controls"])

        self.__controls_panels["volume"] = VolumeBar(player)
        self.pack_end(self.__controls_panels["volume"])

        # Signals
        self.connect("show",self.post_show_action)

    def volume_toggle(self, widget, data = None):
        if self.__current == "pl_controls":
            self.__controls_panels["volume"].show()
            self.__controls_panels["pl_controls"].hide()
            self.__current = "volume"
        else:
            self.__controls_panels["volume"].hide()
            self.__controls_panels["pl_controls"].show()
            self.__current = "pl_controls"

    def post_show_action(self, ui = None):
        self.__controls_panels["volume"].hide()


class ControlsPanel(gtk.VBox):

    def __init__(self,player):
        gtk.VBox.__init__(self)

        # we need it to update play/pause status
        self.__play_pause = PlayPauseButton()
        buttons = [\
                   (PreviousButton(),player.previous), \
                   (self.__play_pause,player.play_toggle),\
                   (StopButton(),player.stop), \
                   (NextButton(),player.next), \
                  ]

        for (button,action) in buttons:
            button.connect("clicked", action)
            self.pack_start(button)

        # Signals
        player.connect("update-status",self.update_status)
        player.connect("connected",self.ui_connected)
        player.connect("disconnected",self.ui_disconnected)

    def ui_disconnected(self, ui):
        for button in self.get_children():
            button.set_sensitive(False)
        self.__play_pause.set_play("stop")

    def ui_connected(self, ui, status):
        for button in self.get_children():
            button.set_sensitive(True)
        self.__play_pause.set_play(status["state"])

    def update_status(self, ui, status):
        self.__play_pause.set_play(status["state"])


class VolumeBar(hildon.VVolumebar):

    def __init__(self,player):
        hildon.VVolumebar.__init__(self)
        self.set_size_request(80,290)
        self.__player = player
        self.__level_signal = None

        self.set_level(0)
        # Signals
        player.connect("update-status",self.update_status)
        player.connect("connected",self.ui_connected)
        player.connect("disconnected",self.ui_disconnected)

    def ui_disconnected(self, ui = None):
        self.set_sensitive(False)
        if self.__level_signal: self.handler_block(self.__level_signal)
        self.set_level(0)
        if self.__level_signal: self.handler_unblock(self.__level_signal)

    def ui_connected(self, ui, status):
        self.set_sensitive(True)
        self.set_level(status["volume"])
        # More Signals
        self.__level_signal = self.connect("level_changed",self.set_volume)
        self.connect("mute_toggled",self.volume_mute_toggle)

    def update_status(self, ui, status):
        if int(self.get_level()) != status["volume"]:
            # we need to update volume bar without send a signal
            self.handler_block(self.__level_signal)
            self.set_level(status["volume"])
            self.handler_unblock(self.__level_signal)

    def set_volume(self,widget):
        self.__player.set_volume(int(self.get_level()))

    def volume_mute_toggle(self,widget):
        pass

#
# Controls Buttons
#

SIZE = gtk.icon_size_register("djmote-control", 72, 72)

class ControlButton(gtk.Button):

    def __init__(self, sensitive = False):
        # The empty string label is there for the image to show on gtk 2.6.10
        gtk.Button.__init__(self, label='')
        self.set_focus_on_click(False)
        self.has_focus = False
        self.set_sensitive(sensitive)
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


class VolumeButton(ControlButton):
    stock_img = stock.DJMOTE_VOLUME


# vim: ts=4 sw=4 expandtab
