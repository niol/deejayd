function $(id) {
  return document.getElementById(id);
}

var VERSION="0.8.3";

var deejaydWebuiTest = function(event) {
    // first hide install extension, not needed
    var doc = window.getBrowser().contentDocument;
    var win = window.getBrowser().contentWindow;
    doc.getElementById("deejayd-webui_install").style.display = "none";

    // see if we need to update extension
    var version = event.target.getAttribute("version");
    if (version != VERSION) {
        doc.getElementById("deejayd-webui_upgrade").style.display = "block";
        return;
        }

    var default_refresh = event.target.getAttribute("refresh");
    var new_server = win.location.href;
    new_server = new_server.replace("http://","").replace("/","");

    var strings = $("webui_strings");
    var prefManager = Components.classes["@mozilla.org/preferences-service;1"]
            .getService(Components.interfaces.nsIPrefBranch);
    // set default refresh
    prefManager.setIntPref("extensions.deejayd-webui.default_refresh",
            default_refresh);
    var list = prefManager.getCharPref("extensions.deejayd-webui.server_list");
    list = list.split("/");
    for (idx in list) {
        if (list[idx] == new_server) {
            prefManager.setCharPref("extensions.deejayd-webui.current_server",
                    new_server);
            openUILink("chrome://deejayd-webui/content/main.xul");
            return;
            }
        }

    var add_new = window.confirm(strings.getFormattedString(
                "addHostConfirm", [new_server]));
    if (add_new) {
        // add server to the list
        var old_list = prefManager.getCharPref(
                "extensions.deejayd-webui.server_list");
        prefManager.setCharPref("extensions.deejayd-webui.server_list",
                old_list+"/"+ new_server);
        prefManager.setCharPref("extensions.deejayd-webui.current_server",
                 new_server);
        openUILink("chrome://deejayd-webui/content/main.xul");
        }
    else {
        // show error message
        doc.getElementById("deejayd-webui_error").style.display = "block";
        }
}

var mainWindow = window.QueryInterface(
                   Components.interfaces.nsIInterfaceRequestor)
                  .getInterface(Components.interfaces.nsIWebNavigation)
                  .QueryInterface(Components.interfaces.nsIDocShellTreeItem)
                  .rootTreeItem
                  .QueryInterface(Components.interfaces.nsIInterfaceRequestor)
                  .getInterface(Components.interfaces.nsIDOMWindow);
mainWindow.document.addEventListener("deejaydEvent",
    function(e) { deejaydWebuiTest(e); }, false, true);

