#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

pip install -r requirements-dev.txt
python setup.py apidoc
mv apidoc/html apidoc/"$CI_COMMIT_REF_NAME"
