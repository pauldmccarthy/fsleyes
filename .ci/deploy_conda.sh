#!/usr/bin/env bash

set -e

rsync -rv dist/conda-bld/ --exclude 'repodata*' --exclude "*json" "condadeploy:"
