#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

pip install -r requirements-dev.txt
python setup.py apidoc
mkdir -p public
mv apidoc/html public/apidoc
