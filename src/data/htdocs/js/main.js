/*
 * main.js
 */

var ajaxdj_ref;

function ajaxdj()
{
    // Activate Debug
    this.debug = false;

    // Internal parms
    this.localeStrings = Array();
    this.message_time = 4000;
    this.config = Array();
    this.config["refresh"] = "0";
    this.refreshEvent = null;

    ajaxdj_ref = this;
    this.ref = 'ajaxdj_ref';

    this.init = function()
    {
        this.uiController = new UIController(this);
        // Send Init request
        this.send_command('init',null,true);
    };

    this.set_busy = function(a)
    {
        if (a) this.uiController.set_busy(a);
        else if (!a && this.busy) this.uiController.set_busy(a);
        this.busy = a;
    };

    this.display_message = function(msg,type)
    {
        this.uiController.display_message(msg, type);
        if (type != 'error') {
            setTimeout(this.ref+'.hide_message()', this.message_time);
            }
    };

    this.hide_message = function()
    {
        this.uiController.hide_message();
    };

    this.http_sockets = new Array();

    this.get_request_obj = function()
    {
        for (var n=0; n<this.http_sockets.length; n++) {
            if (!this.http_sockets[n].busy)
                return this.http_sockets[n];
            }

        var i = this.http_sockets.length;
        this.http_sockets[i] = new http_request();

        return this.http_sockets[i];
    };

    this.send_http_request = function(type, url, parm, lock)
    {
        var request_obj = this.get_request_obj();

        if (request_obj) {
            if (lock) this.set_busy(true);

            request_obj.__lock = lock ? true : false;
            request_obj.onerror = function(o){ ajaxdj_ref.http_error(o); };
            request_obj.oncomplete = function(o){
                    ajaxdj_ref.http_response(o); };
            if (type == 'GET')
                request_obj.GET(url);
            else
                request_obj.POST(url,parm);
            }
    };

    this.send_command = function(command, args, lock)
    {
        var cmd = command;
        if (typeof args == 'object') {
            for (var i in args)
                cmd += '&' + i + '=' + args[i];
            }
        this.send_http_request('GET',
            window.location.href+'commands?action='+cmd,'',lock);
        return false;
    }

    this.send_post_command = function(command,args)
    {
        this.send_http_request('POST',
            window.location.href+'commands?action='+command,args,true);
        return false;
    }

    this.http_error = function(request_obj)
    {
        this.display_message('Error '+ request_obj.responseStatus +
            ' in request : '+request_obj.url, 'error');

        if (request_obj.__lock)
            this.set_busy(false);

        request_obj.reset();
        request_obj.__lock = false;
    };

    this.http_response = function(request_obj)
    {
        if (request_obj.__lock)
            this.set_busy(false);

        this.uiController.set_debug(request_obj.responseText);
        var rs = '';
        var xmldoc = request_obj.responseXML;
        if (xmldoc)
        {
            rs = xmldoc.getElementsByTagName("config").item(0);
            if (rs)
                this.parseConfig(rs);

            rs = xmldoc.getElementsByTagName("locale").item(0);
            if (rs)
                this.parseLocale(rs);

            rs = xmldoc.getElementsByTagName("message").item(0);
            if (rs)
                this.display_message(rs.firstChild.data,
                    rs.getAttribute("type"));

            this.uiController.parseXMLAnswer(xmldoc);
        }
        else
            alert(request_obj.responseText);

        return;
    };

    this.updateMode = function()
    {
        this.send_command("setMode",{mode:$('mode-menu').value},true);
    }

    this.parseConfig = function(config)
    {
        var args = config.getElementsByTagName("arg");
        for (var i=0;arg = args.item(i);i++)
            this.config[arg.getAttribute("name")] = arg.getAttribute("value");

        // Reload refresh
        if (this.refreshEvent) {
            clearInterval(this.refreshEvent);
            this.refreshEvent = null;
            }
        if (this.config["refresh"] != "0")
            this.refreshEvent = setInterval(
                "ajaxdj_ref.send_command('refresh','',false)",
                this.config["refresh"]*'1000');
    };

    this.parseLocale = function(locale)
    {
        var strings = locale.getElementsByTagName("strings");
        for (var i=0;str = strings.item(i);i++)
            this.localeStrings[str.getAttribute("name")] =
                str.getAttribute("value");
    };

    this.getString = function(str)
    {
        if (this.localeStrings[str])
            return this.localeStrings[str];
        else
            return "";
    };

}

window.onload = function(e)
{
    var _ajaxdj = new ajaxdj();
    _ajaxdj.init();
};

window.unload = function(e)
{
    // Save interface config
};
