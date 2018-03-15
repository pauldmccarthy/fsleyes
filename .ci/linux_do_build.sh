#!/bin/bash

set -e

source /build.venv/bin/activate

# Install deps
pip install -r requirements.txt
pip install -r requirements-extra.txt

# Build package
python setup.py build_standalone
mv dist/FSLeyes*.tar.gz dist/FSLeyes-"$CI_COMMIT_REF_NAME"-"$OSNAME".tar.gz

# Sanity check - make sure we can
# start FSLeyes, and run a basic
# test. Sleep between calls to xvfb
# otherwise it gets upset.
apt-get remove -y freeglut3 || yum remove -y freeglut
dist/FSLeyes/fsleyes -V
sleep 5
xvfb-run -s "-screen 0 640x482x24" dist/FSLeyes/fsleyes -S -r .ci/build_test.py
sleep 5
xvfb-run -s "-screen 0 640x480x24" dist/FSLeyes/fsleyes render -vl 8 6 6 -of file.png -sz 572 386 -hc -hl tests/testdata/3d
python tests/compare_images.py file.png tests/testdata/test_screenshot_ortho.png 1000 || true
