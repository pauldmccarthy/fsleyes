#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

source /test.env/bin/activate
pip install ".[doc]"
sphinx-build apidoc public/apidoc
