"""
"""

from deejayd.ui.config import DeejaydConfig

def strEncode(data):
    """Convert a basestring to a valid UTF-8 str."""
    filesystem_charset = DeejaydConfig().get("mediadb","filesystem_charset")
    if isinstance(data, str):
        return data.decode(filesystem_charset, "replace").encode("utf-8")
    elif isinstance(data, unicode):
        return data.encode("utf-8")
    else: 
        return data

def strDecode(data):
    filesystem_charset = DeejaydConfig().get("mediadb","filesystem_charset")
    if isinstance(data, str):
        return data.decode("utf-8", "replace").encode(filesystem_charset)
    elif isinstance(data, unicode):
        return data.encode(filesystem_charset)
    else: 
        return data

# vim: ts=4 sw=4 expandtab
