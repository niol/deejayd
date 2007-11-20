
import dbus

class ScreenMonitor:

    def __init__(self,ui):
        self.__ui = ui
        self.__screen_status = "on"
        bus = dbus.SystemBus(private=True)
        obj = bus.get_object('com.nokia.mce', '/com/nokia/mce/signal')
        iface = dbus.Interface(obj, 'com.nokia.mce.signal')
        iface.connect_to_signal("display_status_ind", self.handler)
        print "Init Screen Monitor"

    def handler(self,status=""):
        print "screen is %s" % (status,)
        if status == "on"  and self.__screen_status == "off" and \
                self.__ui.is_connected():
            self.__ui.update_ui()
        self.__screen_status = status


class ConnectionMonitor:

    def __init__(self,ui):
        self.__ui = ui
        self.bus = dbus.SystemBus(private=True)
        obj = self.bus.get_object('com.nokia.icd', '/com/nokia/icd')
        iface = dbus.Interface(obj, 'com.nokia.icd')
        iface.connect_to_signal("status_changed", self.handler)
        print "Init Connection Monitor"

    def show_connect_dialog(self):
        obj = self.bus.get_object('com.nokia.icd_ui', '/com/nokia/icd_ui')
        iface = dbus.Interface(obj, 'com.nokia.icd_ui')
        iface.show_connect_dialog()

    def handler(self,iap_name="",iap_type="",iap_status="",data=""):
        print """ iap name is %s
                  iap type is %s
                  iap status is %s
                  """ % (iap_name,iap_type,iap_status)
        if iap_type == "WLAN_INFRA" and iap_status in \
                ("DISCONNECTING","SWITCHING"):
            self.__ui.disconnect_to_server()


def init(ui):
    try:
        #mon = ScreenMonitor(ui)
        con = ConnectionMonitor(ui)
    except dbus.DBusException:
        print "Error : unable to init dbus connection"

# vim: ts=4 sw=4 expandtab
