#!/bin/bash

SRCDIR=$(pwd)/$(dirname $0)

makeexec (){
    chmod +x $SRCDIR/$1
}

makeexec scripts/testserver
makeexec tests.py
makeexec debian/rules

# build webui for test
cd webui
cake build

