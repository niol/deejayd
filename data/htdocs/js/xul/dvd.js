// webradio.js

var dvd_ref;

var Dvd = function()
{
    dvd_ref = this;
    this.ref = "dvd_ref";
    this.dropSupport = false;

    this.module = "dvd";
    this.tree = $("dvd-tree");
    // Activate this mode
    $("dvd-source").hidden = false;

    this.init = function() { };

    this.customUpdate = function(dvd)
    {
        $("dvdinfo-box").setAttribute("datasources",window.location.href+"rdf/"+
            this.module+"-"+this.treeId+".rdf");
        $("dvd-description").value = dvd.getAttribute("description");
    };

    /**************************************************************/
    // Event handler
    /**************************************************************/
    this.play = function()
    {
        if (this.tree.contentView) {
            var item = this.tree.contentView.getItemAtIndex(
                        this.tree.currentIndex);
            var str = item.id;
            str = str.split("/")

            var id_value = str[3];
            if (str.length > 4)
                id_value += "."+str[4]

            ajaxdj_ref.send_command("goto",{id:id_value,id_type:"dvd_id"},true);
            }
        return false;
    };

    this.update_langinfo = function()
    {
    }
};

// heritage by prototype
Dvd.prototype = new _Source;

// vim: ts=4 sw=4 expandtab
