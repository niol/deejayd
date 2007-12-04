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

    this.dropAction = function(pos) { fileList_ref.loadItemsInQueue(pos); };

    this.toogleQueue = function()
    {
        var currentState = $('queue-splitter').getAttribute("state");
        if (currentState == "collapsed") {
            $('queue-splitter').setAttribute("state","open");
            $('queue-splitter').style.visibility = "visible";
            $('queue-button').className = "expanded";
            $('queue-clear').style.visibility = "visible";
            }
        else {
            $('queue-splitter').setAttribute("state","collapsed");
            $('queue-button').className = "collapsed";
            $('queue-clear').style.visibility = "hidden";
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
    }
};

// heritage by prototype
Queue.prototype = new CommonTreeManagement;

// vim: ts=4 sw=4 expandtab
