# The following lines require the appropiate tool to be installed.

# Change the default resolution.
#xrandr -s 1920x1200

# Set a background picture.
#xloadimage -onroot -quiet -fullscreen /path/to/bg.jpg

# Allocate some keyboard shortcuts.
#xbindkeys -f /etc/deejayd.xbindkeys

# The last line can contain an X client that will hold the session. It
# ususally is a window manager, but in our case, as we do not need window
# borders for deejayd with a standalone X server, it can be a simple clock.
#exec xdaliclock -24 -noseconds -transparent -fg black -geometry +1400+850
