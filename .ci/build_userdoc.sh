#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

micromamba activate /test.env
pip install git+https://github.com/pauldmccarthy/sphinx_rtd_dark_mode.git@bf/fixes
pip install ".[doc]"
sphinx-build userdoc public/userdoc
