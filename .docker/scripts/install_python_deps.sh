#!/bin/bash

set -e

source /test.venv/bin/activate

pip install --upgrade pip setuptools

$INSTALL_WX

pip install \
    numpy \
    scipy \
    matplotlib \
    six \
    sphinx \
    sphinx-rtd-theme \
    pytest \
    pytest-cov \
    pytest-runner \
    mock \
    coverage \
    pylint \
    flake8 \
    cython
