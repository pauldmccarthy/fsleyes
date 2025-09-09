#!/bin/bash

set -e

projdir=$(pwd)

source /test.venv/bin/activate

pip install --upgrade pip wheel setuptools setuptools-scm twine build packaging
python -m build
twine check dist/*

PIPARGS="--retries 10 --timeout 30"

# install dev versions of core
# dependencies, unless we're
# on a release branch or tag
if [[ "$CI_PROJECT_PATH" != "$UPSTREAM_PROJECT"  || "$CI_COMMIT_REF_NAME" == "main" ]]; then
  pip install $PIPARGS git+https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets.git
  pip install $PIPARGS git+https://git.fmrib.ox.ac.uk/fsl/fslpy.git
  pip install $PIPARGS git+https://git.fmrib.ox.ac.uk/fsl/fsleyes/props.git
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
