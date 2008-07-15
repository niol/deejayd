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

    this.dropAction = function(pos)
    {
        if (this.mediaDragged) {
            // move song at the new position
            var s_ids = this.getTreeSelection("id");
            ajaxdj_ref.send_post_command("queueMove",
                {ids:s_ids, new_pos:pos});
            this.mediaDragged = false;
            }
        else if (panel_ref.mediaDragged) {
            panel_ref.loadInQueue(pos);
            panel_ref.mediaDragged = false;
            }
        else {
            fileList_ref.loadItemsInQueue(pos);
            fileList_ref.dragItemType = null;
            }
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
};

// heritage by prototype
Queue.prototype = new CommonTreeManagement;

// vim: ts=4 sw=4 expandtab
