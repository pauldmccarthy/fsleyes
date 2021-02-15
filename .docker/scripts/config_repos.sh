#!/bin/bash

set -e

echo "deb http://archive.ubuntu.com/ubuntu/  $UBUNTU_VERSION           main restricted universe"  > /etc/apt/sources.list
echo "deb http://security.ubuntu.com/ubuntu/ $UBUNTU_VERSION-security  main restricted universe" >> /etc/apt/sources.list

apt-get update -y
