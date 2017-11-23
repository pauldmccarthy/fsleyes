#!/bin/bash

set -e

if [[ "x$CI_COMMIT_TAG" != "x" ]]; then
  echo "Release detected - patching version - $CI_COMMIT_REF_NAME";
  sed -ie "s/^__version__ = .*$/__version__ = '$CI_COMMIT_REF_NAME'/g" fsleyes/version.py;
fi
