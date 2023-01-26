#!/bin/bash

set -e

add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y $PY_VERSION "$PY_VERSION"-dev $PY_PACKAGES
$PY_VENV /test.venv
source /test.venv/bin/activate

pip install --upgrade pip setuptools wheel
