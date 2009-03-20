// playlist-dialog.js

function arrayRemove(array_obj, from, to) {
  var rest = array_obj.slice((to || from) + 1 || array_obj.length);
  array_obj.length = from < 0 ? array_obj.length + from : from;
  return array_obj.push.apply(array_obj, rest);
};

function $(id) {
  return document.getElementById(id);
}

function createElement(nodeName, attribs, parent_node) {
    var node = document.createElement(nodeName);
    for (attrib in attribs)
        node.setAttribute(attrib, attribs[attrib]);
    if (parent_node != null)
        parent_node.appendChild(node);
    return node;
}

/************************************************************************/
/************************************************************************/

function MagicPlaylist()
{
    this.__id = 0;

    this.init = function()
    {
        this.str = $("dialog_strings");
        if (!window.arguments) {return this.add_filter(null);}
        if (window.arguments[0].title) {
            // update dialog title
            window.title = window.arguments[0].title;
            }
        if (window.arguments[0].input) {
            // set filters
            var filters =
                window.arguments[0].input.getElementsByTagName('filter');
            for (var i=0; filter=filters.item(i); i++) {
                var input_data = {
                    tag: filter.getElementsByTagName('tag').item(0).
                             firstChild.data,
                    op: filter.getElementsByTagName('operator').item(0).
                             firstChild.data,
                    value: filter.getElementsByTagName('value').item(0).
                             firstChild.data,
                    };
                this.add_filter(input_data);
                }
            // set properties
            var properties =
                window.arguments[0].input.getElementsByTagName('property');
            for (var i=0; property=properties.item(i); i++) {
                var id = property.getAttribute('id');
                var value = property.firstChild.data;
                if (id == 'use-or-filter') {
                    var checked = value == "1" ? true : false;
                    $('use-or-filter').checked = checked;
                    }
                else if (id == 'use-limit' && value == "1") {
                    $('limit-checkbox').checked = true;
                    this.update_limit_activation();
                    }
                else if (id == 'limit-value') {
                    $('limit-value').value = value;
                    }
                else if (id == 'limit-sort-value') {
                    $('limit-sort-value').value = value;
                    }
                else if (id == 'limit-sort-direction') {
                    var checked = value == "descending" ? true : false;
                    $('limit-sort-direction').checked = checked;
                    }
                }
            }
        else
            this.add_filter(null);
    };

    this.getString = function(str)
    {
        return this.str.getString(str);
    };

    this.getFormattedString = function(str, values)
    {
        return this.str.getFormattedString(str, values);
    };

    this.__create_select_list = function(list, attrs, parent_node)
    {
        var list_obj = createElement("menulist", attrs, null);
        var popup = createElement("menupopup", {}, list_obj);
        for (idx in list) {
            createElement("menuitem",
                    {label: this.getString(list[idx]),
                     value: list[idx]}, popup);
            }
        if (parent_node != null) { parent_node.appendChild(list_obj); }
        else
            return list_obj;
    };

    this.__create_op_list = function(tag, value, filter)
    {
        var op_list = {
            artist: ["equals", "notequals", "contains", "notcontains"],
            album: ["equals", "notequals", "contains", "notcontains"],
            genre: ["equals", "notequals", "contains", "notcontains"],
            title: ["equals", "notequals", "contains", "notcontains"],
            rating: ["higher", "lower"],
            };

        var select_list = op_list[tag];
        if (select_list) {
            if (value == null)
                value = select_list[0];
            var m = this.__create_select_list(select_list,{value: value},null);
            if (filter != null)
                filter.appendChild(m);
            else
                return m;
            }
    };

    this.__create_value_textbox = function(tag, value, filter)
    {
        var textbox_type = {
            artist: null, album: null, genre: null, title: null,
            rating: "number",
            };
        var node = createElement("textbox", {value: value}, null);
        if (textbox_type[tag])
            node.setAttribute("type", textbox_type[tag])
        if (filter != null)
            filter.appendChild(node);
        else
            return node;
    };

    this.update_filter = function(tag_node)
    {
        var tag = tag_node.value;
        var new_op = this.__create_op_list(tag, null, null);
        tag_node.parentNode.replaceChild(new_op, tag_node.nextSibling);
        var new_textbox = this.__create_value_textbox(tag, "", null);
        tag_node.parentNode.replaceChild(new_textbox, new_op.nextSibling);
    };

    this.add_filter = function(input)
    {
        if (input == null)
            input = {tag: "artist", value: "", op: null};
        var id = this.__set_id();

        var filter_obj = createElement("hbox", {id: "filter-"+id}, null);
        // create tag list
        this.__create_select_list(['title','artist','album','genre','rating'],
                {value: input.tag,
                 oncommand: "magic_pls.update_filter(this);"
                }, filter_obj);
        // create op list
        this.__create_op_list(input.tag, input.op, filter_obj);
        // set value
        this.__create_value_textbox(input.tag, input.value, filter_obj);
        // add remove button
        createElement("button",
                {label: this.getString("remove"),
                 oncommand: "magic_pls.remove_filter(this.parentNode);"
                 }, filter_obj);
        // append filter objetc
        $('filters-box').appendChild(filter_obj);
    };

    this.remove_filter = function(filter_obj)
    {
        filter_obj.parentNode.removeChild(filter_obj);
    };

    this.record = function()
    {
        var output_filter = "";
        var filters = $('filters-box').getElementsByTagName("hbox");
        for (var i=0; filter=filters.item(i); i++) {
            output_filter += "<filter>";
            var tag_list = filter.firstChild;
            output_filter += "<tag>" + tag_list.value + "</tag>";
            var op_list = tag_list.nextSibling;
            output_filter += "<operator>" + op_list.value + "</operator>";
            output_filter += "<value>" + op_list.nextSibling.value + "</value>";
            output_filter += "</filter>";
            }

        var output_prop = "";
        if ($('use-or-filter').checked)
            output_prop += "<property id='use-or-filter'>1</property>";
        if ($('limit-checkbox').checked) {
            output_prop += "<property id='use-limit'>1</property>"
            output_prop += "<property id='limit-value'>" +
                    $('limit-value').value + "</property>";
            output_prop += "<property id='limit-sort-value'>" +
                    $('limit-sort-value').value + "</property>";
            var direction = "ascending";
            if ($('limit-sort-direction').checked)
                direction = "descending";
            output_prop += "<property id='limit-sort-direction'>" +
                direction + "</property>";
            }
        else {
            output_prop += "<property id='use-limit'>0</property>"
            }

        window.arguments[0].output = '<?xml version="1.0"?>'
            + "<magic_playlist>"
            + "<filters>" + output_filter + "</filters>"
            + "<properties>" + output_prop + "</properties>"
            + "</magic_playlist>";
        return true;
    };

    this.update_limit_activation = function()
    {
        var ids = ['limit-value', 'limit-label',
            'limit-sort-value', 'limit-sort-label', 'limit-sort-direction'];
        var enabled = $('limit-checkbox').checked;

        for (idx in ids) { $(ids[idx]).disabled = !enabled; }
    };

    this.__set_id = function()
    {
        this.__id += 1;
        return this.__id;
    };
};

var magic_pls = new MagicPlaylist();
