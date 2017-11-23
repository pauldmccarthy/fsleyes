#!/bin/bash

set -e

# Install python compile-time dependencies
apt-get update -y
apt-get install -y wget
apt-get install -y build-essential
apt-get install -y zlib1g-dev libbz2-dev libnotify-dev libssl-dev libncursesw5-dev libsqlite3-dev libreadline-gplv2-dev libgdbm-dev libc6-dev libpcap-dev libexpat1-dev

# install fsleyes/wxpython runtime dependencies
apt-get install -y freeglut3 libnotify4 libosmesa6 libsdl1.2debian xvfb
apt-get install -y libgtk2.0-0 libgtk-3-0
