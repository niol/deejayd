// fileList.js

var video_ref;

var Video = function()
{
    video_ref = this;
    this.menuId = "video-path";
    this.contextMenuId = false;
    this.updateBox = "video-update";
    this.listType = "video";
    // Activate this mode
    $("video-source").disabled = false;

    this.init = function()
    {
        this.videoInfos=Array("id","title","length","videoheight","videowidth",
            "external_subtitle");
    };

    this.getDir = function(e)
    {
        var args = {};
        if (this.id !='root_link')
            args['video_dir'] = this.id;
        ajaxdj_ref.send_post_command("setvideodir",args);
    };

    this.updateVideoList = function(videoList,dir)
    {
        this.curDir = dir ? dir : "";
        this.constructMenu(dir);
        this.constructItemList(videoList,"video-content");
    };

    this.play = function(item)
    {
        var videoId = item.getAttribute("id");
        ajaxdj_ref.send_command('goto',{ id:videoId },true);
    };

    this.updateInfo = function(selectedItem)
    {
        if (selectedItem) {
            var type = selectedItem.getAttribute("type");
            if (type == "file")
                this.setInfo(selectedItem);
            else
                this.resetInfo();
            }
        else
            this.resetInfo();
    };

    this.setInfo = function(item)
    {
        var infos = Array("videowidth","title","videoheight");
        for (var i in infos) {
            var info = item.getAttribute(infos[i]);
            if (info)
                $("video-"+infos[i]).value = info;
            }

        // Time
        var info = item.getAttribute("length");
        if (info)
            $("video-length").value = formatTime(info);

        // Subtitle
        var format = function(path) {
            var rs = path.split("/");
            return rs[rs.length - 1];
            };
        var info = item.getAttribute("external_subtitle");
        if (info)
            $("video-external_subtitle").value = format(info);
        else
            $("video-external_subtitle").value = "N/A";
    };

    this.resetInfo = function(item)
    {
        for (var i in this.videoInfos) {
            var item = $("video-"+this.videoInfos[i]);
            if (item)
                item.value = "";
            }
    };

    /*************************************/
    /******** Search Part ****************/
    /*************************************/
    this.searchFile = function()
    {
        var text = $('search-text').value;
        var typ = $('search-type').selectedItem.value;
        ajaxdj_ref.send_post_command("search",{type:typ,txt:text});
    };

    this.searchClear = function()
    {
        $('search-text').value = "";
        ajaxdj_ref.send_post_command('getdir',{dir:this.curDir});
    };


/*********************************************************/
/*************  INTERNAL FUNCTIONS ***********************/
/*********************************************************/
    this.customConstructDirRow = function(dirItem)
    {
        dirItem.ondblclick = function(e) {
            ajaxdj_ref.send_post_command("setvideodir",
                { video_dir:e.target.value }); };
    };

    this.constructVideoRow = function(file)
    {
        var fileName = file.firstChild.data;
        var fileItem = document.createElement("listitem");
        fileItem.setAttribute("label",fileName);
        fileItem.setAttribute("type","file");
        fileItem.className = "video-item listitem-iconic";

        for (var i in this.videoInfos) {
            var info = file.getAttribute(this.videoInfos[i]);
            if (info)
                fileItem.setAttribute(this.videoInfos[i],info);
            }

        fileItem.ondblclick = function(e) {
            video_ref.play(e.target) };

        return fileItem;
    };
};

// heritage by prototype
Video.prototype = new CommonList;

// vim: ts=4 sw=4 expandtab
