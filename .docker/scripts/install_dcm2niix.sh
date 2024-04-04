#!/bin/bash

set -e


apt-get update  -y       || yum check-update -y  || true
apt-get install -y unzip || yum install -y unzip || true

mkdir /dcm2niix
cd /dcm2niix
wget https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20240202/dcm2niix_lnx.zip
unzip dcm2niix_lnx.zip
rm dcm2niix_lnx.zip
