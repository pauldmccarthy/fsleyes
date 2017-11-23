#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

python setup.py userdoc
mv userdoc/html userdoc/"$CI_COMMIT_REF_NAME"
