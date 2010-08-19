#!/bin/bash

SRCDIR=$(pwd)/$(dirname $0)

makeexec (){
    chmod +x $SRCDIR/$1
}

makeexec scripts/testserver
makeexec tests.py
makeexec debian/rules

# build webui for text
if [ "$1" ];
then
    python setup.py build_webui --gwt $1 --ant-target build
    cd $SRCDIR/data/htdocs/mobile/
    ln -sf ../../../webui--gwt/deejayd-webui/war/mobile_webui .
    cd $SRCDIR/data/htdocs/webui/
    ln -sf ../../../webui--gwt/deejayd-webui/war/deejayd_webui .
else
    echo "WARNING - You don't enter a GWT SDK Location"
    echo "WARNING - deejayd webui can't be built"
    echo "WARNING - usage: prepare.sh GWT_LOCATION"
fi

if [ -d $SRCDIR/maemosrc ];
then
    makeexec maemosrc/debian/rules

    cd $SRCDIR/maemosrc/deejayd/
    ln -sf ../../deejayd/__init__.py .
    ln -sf ../../deejayd/interfaces.py .
    ln -sf ../../deejayd/mediafilters.py .
    cd $SRCDIR/maemosrc/deejayd/rpc
    ln -sf ../../../deejayd/rpc/jsonbuilders.py .
    ln -sf ../../../deejayd/rpc/jsonparsers.py .
    cd $SRCDIR/maemosrc/deejayd/net
    ln -sf ../../../deejayd/net/client.py .
fi
