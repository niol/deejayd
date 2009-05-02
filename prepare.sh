#!/bin/bash

SRCDIR=$(pwd)/$(dirname $0)

makeexec (){
    chmod +x $SRCDIR/$1
}

makeexec scripts/testserver
makeexec tests.py
makeexec debian/rules


if [ -d $SRCDIR/maemosrc ];
then
    makeexec maemosrc/debian/rules

    cd $SRCDIR/maemosrc/deejayd/
    ln -sf ../../deejayd/__init__.py .
    ln -sf ../../deejayd/interfaces.py .
    ln -sf ../../deejayd/xmlobject.py .
    ln -sf ../../deejayd/mediafilters.py .
    cd $SRCDIR/maemosrc/deejayd/net
    ln -sf ../../../deejayd/net/client.py .
    ln -sf ../../../deejayd/net/xmlbuilders.py .
    ln -sf ../../../deejayd/net/xmlparsers.py .
fi
