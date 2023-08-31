#!/bin/bash

set -e

projdir=$(pwd)

source /test.venv/bin/activate

pip install --upgrade pip wheel setuptools twine build
python -m build
twine check dist/*

PIPARGS="--retries 10 --timeout 30"

# install dev versions of core
# dependencies, unless we're
# on a release branch or tag
if [[ "$CI_PROJECT_PATH" != "$UPSTREAM_PROJECT"  || "$CI_COMMIT_REF_NAME" == "main" ]]; then
  wget https://git.fmrib.ox.ac.uk/fsl/fslpy/-/archive/master/fslpy-master.tar.bz2
  wget https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets/-/archive/master/widgets-master.tar.bz2
  wget https://git.fmrib.ox.ac.uk/fsl/fsleyes/props/-/archive/master/props-master.tar.bz2
  tar xf props-master.tar.bz2   && pushd props-master   && pip install $PIPARGS . && popd
  tar xf fslpy-master.tar.bz2   && pushd fslpy-master   && pip install $PIPARGS . && popd
  tar xf widgets-master.tar.bz2 && pushd widgets-master && pip install $PIPARGS . && popd
fi


pip install dist/*.whl
pushd / > /dev/null
fsleyes -V
fsleyes render -of out1.png $projdir/fsleyes/tests/testdata/3d
pip uninstall -y fsleyes
popd

pip install dist/*.tar.gz
pushd / > /dev/null
fsleyes -V
fsleyes render -of out2.png $projdir/fsleyes/tests/testdata/3d
pip uninstall -y fsleyes
popd
