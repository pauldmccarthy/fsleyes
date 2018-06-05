#!/bin/bash

set -e

pip install wheel
python setup.py sdist
python setup.py bdist_wheel


python3.5 -m venv test.venv
source activate test.venv
pip install dist/*whl
deactivate

rm -r test.venv
python3.5 -m venv test.venv
source activate test.venv
pip install dist/*tar.gz
deactivate
