#!/bin/bash

SRCDIR=$(pwd)/$(dirname $0)

makeexec (){
    chmod +x $SRCDIR/$1
}

makeexec src/scripts/testserver
makeexec src/tests.py
makeexec src/debian/rules

makeexec maemosrc/debian/rules

cd $SRCDIR/maemosrc/deejayd/
ln -sf ../../src/deejayd/__init__.py .
ln -sf ../../src/deejayd/interfaces.py .
ln -sf ../../src/deejayd/xmlobject.py .
ln -sf ../../src/deejayd/mediafilters.py .
cd $SRCDIR/maemosrc/deejayd/net
ln -sf ../../../src/deejayd/net/client.py .
ln -sf ../../../src/deejayd/net/xmlbuilders.py .
ln -sf ../../../src/deejayd/net/xmlparsers.py .
