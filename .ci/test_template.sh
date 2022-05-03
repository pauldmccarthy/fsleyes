#!/bin/bash

set -e

# offscreen tests on macos. We use mesalib,
# as it is not possible to use opengl hw
# accelerated GL on headless macOS
if [[ "$MACOS_OVERLAY_TEST" == "1" ]]; then
  export FSLDIR=~/fsl/fsl-6.0.5/
  ~/miniconda3/bin/conda create -y -c conda-forge -p ./test.env python=3.8 mesalib wget
  source ~/miniconda3/bin/activate ./test.env
  pip install --upgrade pip
else

  apt-get install -y bc

  # Temporary: this should be done
  # in docker image definitions
  apt install -y locales
  locale-gen en_US.UTF-8
  locale-gen en_GB.UTF-8
  update-locale
  export LANG=en_GB.UTF-8

  # We need the FSL atlases for the atlas
  # tests, and need $FSLDIR to be defined
  export FSLDIR=/fsl/
  mkdir -p $FSLDIR/data/
  rsync -rv "fsldownload:$FSL_ATLAS_DIR"    "$FSLDIR/data/atlases/"
  rsync -rv "fsldownload:$FSL_STANDARD_DIR" "$FSLDIR/data/standard/"

  source /test.venv/bin/activate
  pip install --upgrade pip
fi


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

cat requirements.txt | grep -v "fsl" > tmp.txt

# pyopengl-accelerate is not currently
# compatible with python 3.7.
if [[ `python -V` == "Python 3.7"* ]]; then
  cat tmp.txt | grep -iv "pyopengl-accel" > requirements-ci.txt
else
  mv tmp.txt requirements-ci.txt
fi

pip install $PIPARGS -r requirements-ci.txt
pip install $PIPARGS -r requirements-extra.txt
pip install $PIPARGS -r requirements-notebook.txt

tar xf props-master.tar.bz2   && pushd props-master   && pip install $PIPARGS . && popd
tar xf fslpy-master.tar.bz2   && pushd fslpy-master   && pip install $PIPARGS . && popd
tar xf widgets-master.tar.bz2 && pushd widgets-master && pip install $PIPARGS . && popd

# print environment
pip freeze

if [[ "$MACOS_OVERLAY_TEST" == "" ]]; then

  # style stage
  if [ "$TEST_STYLE"x != "x" ]; then pip install $PIPARGS pylint flake8; fi;
  if [ "$TEST_STYLE"x != "x" ]; then flake8                           fsleyes || true; fi;
  if [ "$TEST_STYLE"x != "x" ]; then pylint --output-format=colorized fsleyes || true; fi;
  if [ "$TEST_STYLE"x != "x" ]; then exit 0; fi

  # Run the tests. First batch requires
  # a GUI, so we run via xvfb-run
  ((xvfb-run -a -s "-screen 0 1920x1200x24" pytest --cov-report= --cov-append -m "not (clitest or overlayclitest)" && echo "0" > status) || echo "1" > status) || true
  status=`cat status`
  failed=$status
  sleep 5
fi

# Remaining tests are all off-screen,
# so we can use osmesa
((pytest --cov-report= --cov-append -m "clitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`
sleep 5

# test overlay types for different GL profiles
export FSLEYES_TEST_GL=1.4
((pytest --cov-report= --cov-append -m "overlayclitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`
sleep 5

export FSLEYES_TEST_GL=2.1
((pytest --cov-report= --cov-append -m "overlayclitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`
sleep 5

# GL33-specific tests - only a
# couple of these at the moment
# (overlays/test_overlay_tractogram.py)
export MESA_GL_VERSION_OVERRIDE=3.3
export FSLEYES_TEST_GL=3.3
export LOCAL_TEST_FSLEYES=1
((pytest --cov-report= --cov-append -m "overlayclitest and gl33test" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`

python -m coverage report

exit $failed
