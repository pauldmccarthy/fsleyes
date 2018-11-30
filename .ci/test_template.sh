#!/bin/bash

set -e

apt-get install -y bc

# If running on a fork repository, we merge in the
# upstream/master branch. This is done so that merge
# requests from fork to the parent repository will
# have unit tests run on the merged code, something
# which gitlab CE does not currently do for us.
if [[ "$CI_PROJECT_PATH" != "$UPSTREAM_PROJECT" ]]; then
  git fetch upstream;
  git merge --no-commit --no-ff upstream/master;
fi;

source /test.venv/bin/activate
pip install --upgrade pip

PIPARGS="--retries 10 --timeout 30"

# Make sure we have master branches of the
# core dependencies
wget https://git.fmrib.ox.ac.uk/fsl/fslpy/-/archive/master/fslpy-master.tar.bz2
wget https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets/-/archive/master/widgets-master.tar.bz2
wget https://git.fmrib.ox.ac.uk/fsl/fsleyes/props/-/archive/master/props-master.tar.bz2

pip install $PIPARGS -r requirements-dev.txt

# Install back to front - if we install
# our master versions of the core packages
# first, they might get downgraded during
# a subsequent installation.
#
# pyopengl-accelerate is not currently
# compatible with python 3.7. And it's
# not necessary for testing.
cat requirements.txt | grep -v "fsl" | grep -iv "pyopengl-accel" > requirements-ci.txt
pip install $PIPARGS -r requirements-ci.txt
pip install $PIPARGS -r requirements-extra.txt
pip install $PIPARGS -r requirements-notebook.txt

tar xf props-master.tar.bz2   && pushd props-master   && pip install $PIPARGS . && popd
tar xf fslpy-master.tar.bz2   && pushd fslpy-master   && pip install $PIPARGS . && popd
tar xf widgets-master.tar.bz2 && pushd widgets-master && pip install $PIPARGS . && popd

# print environment
pip freeze

# style stage
if [ "$TEST_STYLE"x != "x" ]; then pip install $PIPARGS pylint flake8; fi;
if [ "$TEST_STYLE"x != "x" ]; then flake8                           fsleyes || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then pylint --output-format=colorized fsleyes || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then exit 0; fi

# Run the tests
export MPLBACKEND=wxagg
export FSLEYES_TEST_GL=2.1
((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "not (clitest or overlayclitest)" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=$status
sleep 5

((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "clitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`
sleep 5

((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "overlayclitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`
sleep 5

# test overlay types for GL14 as well
export FSLEYES_TEST_GL=1.4
((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "overlayclitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`

python -m coverage report

exit $failed
