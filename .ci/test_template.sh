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

# Make sure we have master branches of the
# core dependencies
pip install -r requirements-dev.txt
pip install git+https://git.fmrib.ox.ac.uk/fsl/fslpy.git
pip install git+https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets.git
pip install git+https://git.fmrib.ox.ac.uk/fsl/fsleyes/props.git
cat requirements.txt | grep -v "fsl" > ci-requirements.txt
pip install -r ci-requirements.txt
pip install -r requirements-extra.txt


# style stage
if [ "$TEST_STYLE"x != "x" ]; then pip install pylint flake8; fi;
if [ "$TEST_STYLE"x != "x" ]; then flake8                           fsleyes || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then pylint --output-format=colorized fsleyes || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then exit 0; fi

# Run the tests  - test overlay types for GL14 as well
export MPLBACKEND=wxagg
export FSLEYES_TEST_GL=2.1
((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "not clitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=$status
sleep 5

((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "clitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`
sleep 5

export FSLEYES_TEST_GL=1.4
((xvfb-run -s "-screen 0 640x480x24" pytest --cov-report= --cov-append -m "clitest" && echo "0" > status) || echo "1" > status) || true
status=`cat status`
failed=`echo "$status + $failed" | bc`

python -m coverage report

exit $failed
