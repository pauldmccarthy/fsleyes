#!/bin/bash

set -e

mkdir /dcm2niix
cd /dcm2niix
wget https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20250506/dcm2niix_lnx.zip
unzip dcm2niix_lnx.zip
rm dcm2niix_lnx.zip

