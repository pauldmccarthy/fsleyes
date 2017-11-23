#!/bin/bash

set -e

pip install setuptools wheel twine
twine upload dist/*whl dist/*tar.gz
