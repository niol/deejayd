#!/bin/sh

chmod +x src/scripts/testserver
chmod +x src/debian/rules

chmod +x maemosrc/debian/rules
cd maemosrc/deejayd/net
ln -sf ../../../src/deejayd/net/client.py .
ln -sf ../../../src/deejayd/net/xmlbuilders.py .
