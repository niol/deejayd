/*
 * ajax.js
 * class for http request
 */

function http_request()
{
    this.url = '';
    this.busy = false;
    this.xmlhttp = null;

    this.reset = function()
    {
        // set unassigned event handlers
        this.onloading = function(){ };
        this.onloaded = function(){ };
        this.oninteractive = function(){ };
        this.oncomplete = function(){ };
        this.onabort = function(){ };
        this.onerror = function(){ };

        this.url = '';
        this.busy = false;
        this.xmlhttp = null;
    };

    this.build = function()
    {
        if (window.XMLHttpRequest)
            this.xmlhttp = new XMLHttpRequest();
        else if (window.ActiveXObject)
            this.xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    };

    this.GET = function(url)
    {
        this.build();

        if (!this.xmlhttp) {
            this.onerror(this);
            return false;
        }

        var ref = this;
        this.url = url;
        this.busy = true;

        this.xmlhttp.onreadystatechange = function(){
                ref.xmlhttp_onreadystatechange(); };
        this.xmlhttp.open('GET', url);
        return this.xmlhttp.send(null);
    };

    this.POST = function(url,parm)
    {
        this.build();

        if (!this.xmlhttp) {
            this.onerror(this);
            return false;
            }

        var ref = this;
        this.url = url;
        this.busy = true;


        this.xmlhttp.onreadystatechange = function(){
            ref.xmlhttp_onreadystatechange(); };
        this.xmlhttp.open('POST', url);

        var toSend = '';
        if (typeof parm == 'object') {
            this.xmlhttp.setRequestHeader('Content-Type',
                                          'application/x-www-form-urlencoded');

            for (var i in parm) {
                if (typeof parm[i] == 'object') {
                    var obj = parm[i];
                    for (var j in obj)
                        toSend += (toSend?'&':'') + i + '=' + urlencode(obj[j]);
                    }
                else
                    toSend += (toSend? '&' : '') + i + '=' + urlencode(parm[i]);
                }
            }
        else
            toSend = parm;

        return this.xmlhttp.send(toSend);
    };

    this.xmlhttp_onreadystatechange = function()
    {
        if(this.xmlhttp.readyState == 1)
            this.onloading(this);

        else if(this.xmlhttp.readyState == 2)
            this.onloaded(this);

        else if(this.xmlhttp.readyState == 3)
            this.oninteractive(this);

        else if(this.xmlhttp.readyState == 4) {
            this.responseText = this.xmlhttp.responseText;
            this.responseXML = this.xmlhttp.responseXML;

            if(this.xmlhttp.status == 0)
                this.onabort(this);
            else if(this.xmlhttp.status == 200)
                this.oncomplete(this);
            else
                this.onerror(this);

            this.busy = false;
            }
    };

    // a best way to take http header
    this.get_header = function(name)
    {
        return this.xmlhttp.getResponseHeader(name);
    };

    this.reset();
}
