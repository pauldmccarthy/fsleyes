#!/bin/bash

set -e

pip install wheel
python setup.py sdist
python setup.py bdist_wheel
