
var prefManager = Components.classes["@mozilla.org/preferences-service;1"]
            .getService(Components.interfaces.nsIPrefBranch);

function $(id) {
  return document.getElementById(id);
}

function load()
{
    // load server list
    var hosts=prefManager.getCharPref("extensions.deejayd-webui.server_list");
    hosts = hosts.split("/");
    for (idx in hosts) {
        if (hosts[idx] != "")
            $("server-list").appendItem(hosts[idx], hosts[idx])
        }

    // load ui options
    var refresh = prefManager.getIntPref("extensions.deejayd-webui.refresh");
    $("refresh-time").value = refresh;
    var use_default = prefManager.getBoolPref(
            "extensions.deejayd-webui.use_default_refresh");
    $("ref-check").checked = use_default;
    $("refresh-time").disabled = use_default;
}

function save()
{
    // save server list
    var servers = "";
    for (var i=0; i<$("server-list").getRowCount(); i++) {
        var item = $("server-list").getItemAtIndex(i);
        servers += "/" + item.value;
        }
    prefManager.setCharPref("extensions.deejayd-webui.server_list",servers);
    // save refresh
    prefManager.setBoolPref("extensions.deejayd-webui.use_default_refresh",
            $("ref-check").checked);
    if (!$("ref-check").checked)
        prefManager.setIntPref("extensions.deejayd-webui.refresh",
                $("refresh-time").value);
    // we finish to save, close window
    window.close();
}

var serverHost = {
    add: function() {
         var host = $("server-host").value;
         var port = $("server-port").value;
         if (host && port) {
             $("server-list").appendItem(host+":"+port, host+":"+port)
             $("server-host").reset();
             $("server-port").value = 6880;
             }
         },
    remove: function() {
         if ($("server-list").selectedIndex != -1)
             $("server-list").removeItemAt($("server-list").selectedIndex);
         },
};

