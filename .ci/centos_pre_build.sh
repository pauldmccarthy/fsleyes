#!/bin/bash

set -e

yum check-update -y || true
yum install -y epel-release

# Install compilers and dependencies
# for compiling Python
yum groupinstall -y "Development tools"
yum install -y wget zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel gdbm-devel libpcap-devel xz-devel expat-devel

# install fsleyes/wxpython runtime dependencies
yum install -y freeglut libnotify mesa-libOSMesa SDL xorg-x11-server-Xvfb

# install wxpython compile-time dependencies.
# We currently have to compile wx from source
# because, on centos6, there is no
# python 3.5/wxpython binary wheel available
# for download.
if [ "$WXPYTHON_CENTOS_GTK" == "gtk3" ]; then
  yum install -y gtk3-devel webkitgtk3-devel;
else
  yum install -y gtk2-devel webkitgtk-devel;
fi;

yum install -y libjpeg-turbo-devel libtiff-devel SDL-devel gstreamer-plugins-base-devel libnotify-devel freeglut-devel
