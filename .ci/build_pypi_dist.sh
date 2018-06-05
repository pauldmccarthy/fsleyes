#!/bin/bash

set -e

pip install wheel
python setup.py sdist
python setup.py bdist_wheel


python3.5 -m venv pypi_test.venv
source activate pypi_test.venv
pip install dist/*whl
deactivate

rm -r pypi_test.venv
python3.5 -m venv pypi_test.venv
source activate pypi_test.venv
pip install dist/*tar.gz
deactivate
