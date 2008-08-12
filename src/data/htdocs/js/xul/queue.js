// queue.js

var queue_ref;

var Queue = function()
{
    queue_ref = this;
    this.module = "queue";
    this.tree = $("queue-tree");

    var queueController = {
        supportsCommand : function(cmd){
            return (cmd == "cmd_delete"); },
        isCommandEnabled : function(cmd){ return true; },
        doCommand : function(cmd){
            if (cmd == "cmd_delete")
                queue_ref.remove();
            },
        onEvent : function(evt){ }
        };

    this.customUpdate = function(queue)
    {
        $("queue-description").value = queue.getAttribute("description");
        return true;
    };

    this.toogleQueue = function()
    {
        var currentState = $('queue-splitter').getAttribute("state");
        if (currentState == "collapsed") {
            $('queue-splitter').setAttribute("state","open");
            $('queue-splitter').style.visibility = "visible";
            $('queue-button').className = "expanded";
            $('queue-actions').style.visibility = "visible";
            }
        else {
            $('queue-splitter').setAttribute("state","collapsed");
            $('queue-button').className = "collapsed";
            $('queue-actions').style.visibility = "hidden";
            $('queue-splitter').style.visibility = "collapse";
            }
    };

    this.play = function()
    {
        if (this.tree.contentView) {
            var item = this.tree.contentView.getItemAtIndex(
                            this.tree.currentIndex);
            var str = item.id;
            ajaxdj_ref.send_command("goto",{ source:"queue",
                                    id:str.split("/")[3] },true);
            }
    };

    this.toggle_random = function()
    {
        if ($('queue-playorder').checked)
            var state = "random";
        else
            var state = "inorder";
        ajaxdj_ref.send_post_command("playorder",{source:"queue",value:state});
        return false;
    };

    /********************************************************************/
    // custom drag and drop actions
    /********************************************************************/
    this.supportedDropData = Array('queue', 'panel', 'playlist-list',
                                   'directory-list', 'audio-file-list',
                                   'panel-playlist');
    this.dropAction = function(pos, data)
    {
        if (data == "queue") {
            // move song at the new position
            var s_ids = queue_ref.getTreeSelection("id");
            ajaxdj_ref.send_post_command("queueMove",{ids:s_ids, new_pos:pos});
            }
        else if (data == "panel" || data == "panel-playlist") {
            panel_ref.loadInQueue(pos);
            }
        else if ((data == 'directory-list') || (data == 'audio-file-list')) {
            fileList_ref.loadFilesInQueue(pos);
            }
        else if (data == 'playlist-list') {
            fileList_ref.loadPlaylistInQueue(pos);
            }
    };
};
// heritage by prototype
Queue.prototype = new _Source;

// vim: ts=4 sw=4 expandtab
