#!/bin/bash

set -e

apt-get install -y libgconf2-dev
apt-get install -y build-essential \
                   libgtk2.0-dev \
                   libwebkitgtk-dev \
                   libjpeg-dev \
                   libtiff-dev \
                   libsdl-dev \
                   libgstreamer0.10-dev \
                   libgstreamer-plugins-base0.10-dev \
                   libnotify-dev \
                   freeglut3-dev

mkdir $VIRTUAL_ENV/wx-build
pushd $VIRTUAL_ENV/wx-build

wget https://sourceforge.net/projects/wxpython/files/wxPython/3.0.2.0/wxPython-src-3.0.2.0.tar.bz2

tar xf wxPython-src-3.0.2.0.tar.bz2

cd wxPython-src-3.0.2.0/wxPython

find src     -name "*.cpp" | xargs sed -ie 's/PyErr_Format(PyExc_RuntimeError, mesg);/PyErr_Format(PyExc_RuntimeError, "%s", mesg);/g'
find contrib -name "*.cpp" | xargs sed -ie 's/PyErr_Format(PyExc_RuntimeError, mesg);/PyErr_Format(PyExc_RuntimeError, "%s", mesg);/g'

python ./build-wxpython.py \
--install \
--installdir=/ \
--prefix=$VIRTUAL_ENV \
--wxpy_installdir=$VIRTUAL_ENV

export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH

popd
