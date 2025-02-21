#!/bin/bash

set -e

# offscreen tests on macos. We use mesalib,
# as it is not possible to use opengl hw
# accelerated GL on headless macOS
if [[ "$MACOS_OVERLAY_TEST" == "1" ]]; then
  export FSLDIR=~/fsl/fsl-for-fsleyes-tests/
  eval "$(~/micromamba/bin/micromamba shell hook --shell $(basename ${SHELL}))"
  micromamba create -y -c conda-forge -p ./test.env python=3.11 zstd mesalib wget libiconv
  micromamba activate ./test.env
  pip install --upgrade pip
else

  # We need the FSL atlases for the atlas
  # tests, and need $FSLDIR to be defined
  export FSLDIR=/fsl/
  mkdir -p $FSLDIR/data/
  rsync -rv "fsldownload:$FSL_ATLAS_DIR"    "$FSLDIR/data/atlases/"
  rsync -rv "fsldownload:$FSL_STANDARD_DIR" "$FSLDIR/data/standard/"

  source /test.venv/bin/activate
  pip install --upgrade pip setuptools wheel build
fi

PIPARGS=" --retries 10 "
PIPARGS+="--timeout 30 "
PIPARGS+="--trusted-host files.pythonhosted.org "
PIPARGS+="--trusted-host pypi.org "

# Make sure we have latest (possibly development)
# versions of the core dependencies
pip install $PIPARGS git+https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets.git
pip install $PIPARGS git+https://git.fmrib.ox.ac.uk/fsl/fslpy.git
pip install $PIPARGS git+https://git.fmrib.ox.ac.uk/fsl/fsleyes/props.git

# install fsleyes+dependencies
pip install $PIPARGS ".[extra,test,style]"

# Run CI debugging commands
${FSLEYES_CI_PRE_TEST_COMMAND}

# print environment
pip freeze

# fsleyes/tests do not get installed into env,
# so put the local folder on the $PYTHONPATH
export PYTHONPATH=$(pwd)

# Jupyter notebook will not start when run
# as root, unless we add another setting.
export FSLEYES_EXTRA_JUPYTER_CONFIG="c.ServerApp.allow_root = True"

PYTEST_EXTRA_ARGS=($PYTEST_EXTRA_ARGS)

if [[ "$MACOS_OVERLAY_TEST" == "" ]]; then

  # style stage
  if [ "$TEST_STYLE"x != "x" ]; then flake8                           fsleyes || true; fi;
  if [ "$TEST_STYLE"x != "x" ]; then pylint --output-format=colorized fsleyes || true; fi;
  if [ "$TEST_STYLE"x != "x" ]; then exit 0; fi

  # Run the tests. First batch requires a
  # GUI, so we run via xvfb-run The jupyter
  # notebook tests are flaky, and fail
  # non-deterministically under docker for
  # unknown reasons, so we run them
  # separately.
  ((xvfb-run -a -s "-screen 0 1920x1200x24" pytest ${PYTEST_EXTRA_ARGS[@]} --cov-report= --cov-append -k "not test_notebook" -m "not (clitest or overlayclitest)" && echo "0" > status) || echo "1" > status) || true
  ((xvfb-run -a -s "-screen 0 1920x1200x24" pytest ${PYTEST_EXTRA_ARGS[@]} --cov-report= --cov-append fsleyes/tests/actions/test_notebook.py && echo "0" > status) || echo "1" > status) || true
  status=`cat status`
  failed=$status
  sleep 5
else
  failed=0
fi

# Remaining tests are all off-screen,
# so we don't need xvfb
((pytest ${PYTEST_EXTRA_ARGS[@]} --cov-report= --cov-append -m "clitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`

# Test overlay types for different GL profiles -
# gl14 first Support for GL14 is flaky in new
# mesa+macOS versions - regular segfaults.
if [[ "$MACOS_OVERLAY_TEST" == "" ]]; then
  export FSLEYES_TEST_GL=1.4
  ((pytest ${PYTEST_EXTRA_ARGS[@]} --cov-report= --cov-append -m "overlayclitest" && echo "0" > status) || echo "1" > status) || true
  status=`cat status`
  failed=`echo "$status + $failed" | bc`
fi

# gl21 compatibility
export MESA_GL_VERSION_OVERRIDE=2.1
export FSLEYES_TEST_GL=2.1
((pytest ${PYTEST_EXTRA_ARGS[@]} --cov-report= --cov-append -m "overlayclitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`

# GL33-specific tests
export MESA_GL_VERSION_OVERRIDE=3.3
export FSLEYES_TEST_GL=3.3
export LOCAL_TEST_FSLEYES=1
((pytest ${PYTEST_EXTRA_ARGS[@]} --cov-report= --cov-append -m "overlayclitest and gl33test" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`

python -m coverage report

exit $failed
