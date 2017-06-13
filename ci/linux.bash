#!/bin/bash

set -o errexit

[[ $(uname) != 'Linux' ]] && exit

#pushd /tmp

twodigitsversion=$(echo $VERSION | cut -c 1-3)

urldir=https://downloadarchive.documentfoundation.org/libreoffice/old/$VERSION/deb/x86_64
filename=LibreOffice_${VERSION}_Linux_x86-64_deb
python_bin=/opt/libreoffice${twodigitsversion}/program/python

if [ ! -f ${filename}.tar.gz ]; then
    wget $urldir/${filename}.tar.gz
fi
if [ ! -d ${filename} ]; then
    tar xvf ${filename}.tar.gz
fi
if [ ! -f ${python_bin} ]; then
    dpkg -i Lib*_Linux_x86-64*deb*/DEBS/*.deb
fi
