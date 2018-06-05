#!/bin/bash

set -e

source /test.venv/bin/activate

pip install wheel
python setup.py sdist
python setup.py bdist_wheel

pip install dist/*.whl
pip uninstall -y fsleyes

pip install dist/*.tar.gz
pip uninstall -y fsleyes
