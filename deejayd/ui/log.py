from twisted.python import log
from deejayd.ui.config import DeejaydConfig

ERROR = 0
INFO = 1
DEBUG = 2

level = DeejaydConfig().get("general","log")
log_level = {"error": ERROR, "info": INFO, \
             "debug": DEBUG}[level]


def err(err):
    log.err("ERROR - " + err)

def msg(msg):
    log.msg(msg)

def info(msg):
    if log_level >= INFO:
        log.msg("INFO - " + msg)

def debug(msg):
    if log_level >= DEBUG:
        log.msg("DEBUG - "+ msg)

# vim: ts=4 sw=4 expandtab
