#!/bin/bash

set -e

source /build.venv/bin/activate

# Install deps
pip install -r requirements.txt

# Build package
python setup.py build_standalone
mv dist/FSLeyes*.tar.gz dist/FSLeyes-"$CI_COMMIT_REF_NAME"-"$OSNAME".tar.gz

# Sanity check - make sure we can
# start FSLeyes, and run a basic
# test. Sleep between calls to xvfb
# otherwise it gets upset.
apt-get remove -y freeglut3 || yum remove -y freeglut
xvfb-run -s "-screen 0 640x480x24" dist/FSLeyes/fsleyes -V
sleep 5
xvfb-run -s "-screen 0 640x482x24" dist/FSLeyes/fsleyes -S -r .ci/build_test.py
sleep 5
xvfb-run -s "-screen 0 640x480x24" dist/FSLeyes/fsleyes render -of file.png -sz 572 386 -hc -hl tests/testdata/MNI152_T1_2mm_brain
python tests/compare_images.py file.png tests/testdata/test_screenshot_ortho.png 1000
