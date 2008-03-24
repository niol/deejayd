// fileList.js

var videolist_ref;
var videolib_ref;

var VideoLibrary = function()
{
    videolib_ref = this;
    this.tree = $("videodir-tree");
    this.updateBox = "video-update";
    this.treeId = -1

    this.updateDir = function(obj)
    {
        var id = parseInt(obj.getAttribute("id"));
        if (id != this.treeId) {
            this.treeId = id;
            // clear selection
            if (this.tree.view)
                this.tree.view.selection.clearSelection();
            // Update datasources
            this.tree.setAttribute("datasources",window.location.href+"rdf/"+
                "videodir-"+id+".rdf");
            }
    };

    this.setDirectory = function(evt)
    {
        var childElement = {}, rowObject = {}, columnObject = {};
        this.tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
            columnObject, childElement);

        if (columnObject.value && rowObject.value != -1) {
            if (columnObject.value.index != 1)
                return true;
            var dir_item = this.tree.contentView.getItemAtIndex(
                                rowObject.value);
            var dir = dir_item.id.replace("http://videodir/root/", "");
            ajaxdj_ref.send_post_command("videoset",
                {type:"directory", value:dir});
            }
        return true;
    };

    this.search = function()
    {
        var text = $('videosearch-text').value;
        if (text != "")
            ajaxdj_ref.send_post_command("videoset",{type:"search",value:text});
    };

    this.updateDatabase = function(upObj)
    {
        var progress = upObj.getAttribute("p");
        var upId = upObj.firstChild.data;
        if (progress == "1") {
            $(this.updateBox).selectedIndex = 1
            $('video-update-progressbar').mode = "undetermined";
            setTimeout(
                "ajaxdj_ref.send_command('video_update_check',{id:"+upId+
                "},false)",1000);
            }
        else {
            $(this.updateBox).selectedIndex = 0
            $('video-update-progressbar').mode = "determined";
            }
    };
}


var VideoList = function()
{
    videolist_ref = this;
    this.ref = "videolist_ref";

    this.mediaDragged = true;
    this.module = "video";
    this.tree = $("video-tree");
    // Activate this mode
    $("video-source").disabled = false;

    this.treeController = false;
    this.customUpdate = function(video)
    {
        $("videolist-description").value = video.getAttribute("description");
        return true;
    };
};
// heritage by prototype
VideoList.prototype = new CommonTreeManagement;

// vim: ts=4 sw=4 expandtab
