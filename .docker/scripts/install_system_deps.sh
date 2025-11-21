#!/bin/bash

set -e

apt-get update  -y
apt-get install -y --ignore-missing \
  software-properties-common \
  xvfb \
  bzip2 \
  curl \
  wget \
  rsync \
  git \
  unzip \
  bc \
  openssh-client

apt install -y locales
locale-gen en_US.UTF-8
locale-gen en_GB.UTF-8
update-locale

apt -y clean
apt -y autoremove
rm -rf /var/lib/apt/lists/*
