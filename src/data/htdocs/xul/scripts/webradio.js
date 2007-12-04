// webradio.js

var webradio_ref;

var Webradio = function()
{
    webradio_ref = this;
    this.module = "webradio";
    this.tree = $("webradio-tree");
    // Activate this mode
    $("webradio-source").disabled = false;

    this.treeController = {
        supportsCommand : function(cmd){
            return (cmd == "cmd_delete"); },
        isCommandEnabled : function(cmd){return true;},
        doCommand : function(cmd){
            if (cmd == "cmd_delete")
                webradio_ref.removeItems();
            },
        onEvent : function(evt){ }
        };

    this.customUpdate = function(webradio)
    {
        $("webradio-description").value =
                    webradio.getAttribute("description");
        return true;
    };

    this.add = function()
    {
        var nameParm = $('webradio-name').value;
        var urlParm = $('webradio-url').value;

        if (!nameParm || !urlParm) {
            alert(ajaxdj_ref.getString('missParm'));
            return;
            }
        ajaxdj_ref.send_post_command('webradioAdd',
            {name: nameParm, url: urlParm},true);

        // Clear form
        $('webradio-name').value = "";
        $('webradio-url').value = "";
    };
};

// heritage by prototype
Webradio.prototype = new CommonTreeManagement;

// vim: ts=4 sw=4 expandtab
