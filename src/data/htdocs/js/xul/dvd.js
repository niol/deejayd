// webradio.js

var dvd_ref;

var Dvd = function()
{
    dvd_ref = this;
    this.ref = "dvd_ref";

    this.module = "dvd";
    this.tree = $("dvd-tree");
    // Activate this mode
    $("dvd-source").hidden = false;

    this.init = function() { };

    this.customUpdate = function(webradio)
    {
        $("dvdinfo-box").setAttribute("datasources",window.location.href+"rdf/"+
            this.module+"-"+this.treeId+".rdf");
        return true;
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
Dvd.prototype = new CommonTreeManagement;

// vim: ts=4 sw=4 expandtab