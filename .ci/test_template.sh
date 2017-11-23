#!/bin/bash

set -e


# Install $PY_VERSION, xvfb, and all
# of the wxpython dependencies.
apt-get update -y || true
apt-get install -y software-properties-common python-software-properties xvfb libgtk2.0-0 libgtk-3-0 libnotify4 freeglut3 libsdl1.2debian bzip2
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y || true
apt-get install -y $PY_VERSION "$PY_VERSION"-dev $PY_PACKAGES
$PY_VENV test.venv
source test.venv/bin/activate
pip install --upgrade pip setuptools

# If running on a fork repository, we merge in the
# upstream/master branch. This is done so that merge
# requests from fork to the parent repository will
# have unit tests run on the merged code, something
# which gitlab CE does not currently do for us.
if [[ "$CI_PROJECT_PATH" != "$UPSTREAM_PROJECT" ]]; then
  git fetch upstream;
  git merge --no-commit --no-ff upstream/master;
fi;

$INSTALL_WX

# All other deps can be installed as normal.
# We install test dependenciesd through pip,
# because if we let setuptools do it, it
# will build/install everything from source,
# rather than using wheels.
pip install -r requirements.txt
pip install sphinx sphinx-rtd-theme
pip install pytest pytest-cov pytest-html pytest-runner mock coverage

# style stage
if [ "$TEST_STYLE"x != "x" ]; then pip install pylint flake8; fi;
if [ "$TEST_STYLE"x != "x" ]; then flake8                           fsleyes || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then pylint --output-format=colorized fsleyes || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then exit 0; fi

# Run the tests. If we don't set the
# matplotlib backend, matplotlib will
# try and access tkinter, which doesn't
# exist.
MPLBACKEND='wxagg' xvfb-run -s "-screen 0 640x480x24" python setup.py test
