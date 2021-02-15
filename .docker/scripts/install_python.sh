#!/bin/bash

set -e

add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y $PY_VERSION "$PY_VERSION"-dev $PY_PACKAGES
$PY_VENV /test.venv
source /test.venv/bin/activate

# install an older setuptools to work around
# an issue with newer versions:
#   https://github.com/wxWidgets/Phoenix/issues/1769
pip install --upgrade pip setuptools==45
