#!/bin/bash

set -e

source /test.venv/bin/activate

pip install --upgrade pip setuptools

$INSTALL_WX

pip install \
    numpy \
    scipy \
    matplotlib \
    sphinx \
    sphinx-rtd-theme \
    coverage \
    pytest \
    pytest-cov \
    coverage \
    pylint \
    flake8
