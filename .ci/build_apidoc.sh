#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

source /test.venv/bin/activate
pip install git+https://github.com/pauldmccarthy/sphinx_rtd_dark_mode.git@bf/fixes
pip install ".[doc]"
sphinx-build apidoc public/apidoc
