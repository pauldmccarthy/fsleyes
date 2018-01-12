#!/bin/bash

set -e

python3.5 -m venv fsleyes-build-venv
. fsleyes-build-venv/bin/activate
pip install numpy
pip install --pre "$WXPYTHON_VERSION"
pip install --no-binary ":all:" "pyopengl>=3.1.0,<4.0" "pyopengl-accelerate>=3.1.0,<4.0"
pip install -r requirements.txt
pip install -r requirements-extra.txt
pip install -r requirements-dev.txt
pip install "py2app==0.14"
pip install sphinx sphinx-rtd-theme mock

# Patch/rebuild py2app (see setup.py docstring)
PY2APP=`python -c "import py2app; print(py2app.__file__)"`
BUILDDIR=`pwd`
pushd `dirname $PY2APP`
patch -p2 < "$BUILDDIR"/assets/build/py2app.patch
pushd apptemplate
python setup.py
popd
popd
python setup.py build_standalone
mv dist/FSLeyes*.tar.gz dist/FSLeyes-"$CI_COMMIT_REF_NAME"-macos.tar.gz

# Sanity check - make sure we can start
# FSLeyes. Assuming here that we have a
# display on the mac build environment
dist/FSLeyes.app/Contents/MacOS/fsleyes -V
dist/FSLeyes.app/Contents/MacOS/fsleyes render -of file.png -sz 572 386 -hc -hl tests/testdata/MNI152_T1_2mm_brain
python tests/compare_images.py file.png tests/testdata/test_screenshot_ortho.png 1000

deactivate
rm -r fsleyes-build-venv
