#!/bin/bash

set -o errexit

[[ $(uname) != 'Darwin' ]] && exit

urldir=https://downloadarchive.documentfoundation.org/libreoffice/old/$VERSION/mac/x86_64
filename=LibreOffice_${VERSION}_MacOS_x86-64.dmg
python_bin=/Applications/LibreOffice.app/Contents/MacOS/python

if [ ! -f $(filename) ]; then
    wget $urldir/$filename
fi
if [ ! -f $(python_bin) ]; then
    sudo hdiutil attach $filename
fi

