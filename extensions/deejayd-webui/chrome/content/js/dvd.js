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
    };

    /**************************************************************/
    // Event handler
    /**************************************************************/
    this.update_langinfo = function()
    {
    }
};

// heritage by prototype
Dvd.prototype = new _Source;

// vim: ts=4 sw=4 expandtab
