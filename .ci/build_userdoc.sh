#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

source /test.venv/bin/activate
pip install ".[doc]"
sphinx-build userdoc public/userdoc
