#!/bin/bash

SRCDIR=$(dirname $0)

makeexec (){
    chmod +x $SRCDIR/$1
}

makeexec src/scripts/testserver
makeexec src/tests.py
makeexec src/debian/rules

makeexec maemosrc/debian/rules

cd $SRCDIR/maemosrc/deejayd/net
ln -sf ../../../src/deejayd/net/client.py .
ln -sf ../../../src/deejayd/net/xmlbuilders.py .
