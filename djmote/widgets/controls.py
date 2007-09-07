import gtk,hildon
from djmote import stock

class ControlBox(gtk.VBox):

    def __init__(self,player):
        gtk.VBox.__init__(self)

        vol_button = VolumeButton()
        vol_button.connect("clicked",self.volume_toggle)
        self.pack_end(vol_button)

        self.__current = "pl_controls"
        self.controls_panels = {"volume":VolumeBar(player),\
                                "pl_controls": ControlsPanel(player),} 

        for panel in self.controls_panels.values():
            self.pack_end(panel)

    def volume_toggle(self, widget, data = None):
        if self.__current == "pl_controls":
            self.controls_panels["volume"].show()
            self.controls_panels["pl_controls"].hide()
            self.__current = "volume"
        else:
            self.controls_panels["volume"].hide()
            self.controls_panels["pl_controls"].show()
            self.__current = "pl_controls"

    def update_status(self,status):
        self.controls_panels["pl_controls"].set_player_state(status['state'])
        self.controls_panels["volume"].update(status['volume'])

    def post_show_action(self):
        self.controls_panels["volume"].hide()


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

    def set_player_state(self,state):
        self.__play_pause.set_play(state)


class VolumeBar(hildon.VVolumebar):

    def __init__(self,player):
        hildon.VVolumebar.__init__(self)
        self.set_size_request(80,300)
        self.__player = player
        self.__volume_init = False

    def update(self,volume):
        if not self.__volume_init:
            self.set_level(volume)
            self.connect("level_changed",self.set_volume)
            self.connect("mute_toggled",self.volume_mute_toggle)

    def set_volume(self,widget):
        self.__player.set_volume(int(self.get_level()))

    def volume_mute_toggle(self,widget):
        pass

#
# Controls Buttons
#

SIZE = gtk.icon_size_register("djmote-control", 72, 72)

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


class VolumeButton(ControlButton):
    stock_img = stock.DJMOTE_VOLUME


# vim: ts=4 sw=4 expandtab
