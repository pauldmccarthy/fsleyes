#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

pip install -r requirements-dev.txt
python setup.py userdoc
mkdir -p public
mv userdoc/html public/userdoc
