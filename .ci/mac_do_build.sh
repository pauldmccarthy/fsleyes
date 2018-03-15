#!/bin/bash

set -e

VENV_DIR=fsleyes-venv/path/to/an/environment/with/a/very/long/name/to/make/sure/that/py2app/does/not/complain/fsleyes-build-venv

python3.5 -m venv $VENV_DIR
. $VENV_DIR/bin/activate
pip install numpy
pip install --no-binary scipy "scipy>=0.18,<2"
pip install "$WXPYTHON_VERSION"
pip install --no-binary ":all:" "pyopengl>=3.1.0,<4.0" "pyopengl-accelerate>=3.1.0,<4.0"
pip install -r requirements.txt
pip install -r requirements-extra.txt
pip install -r requirements-dev.txt
pip install "py2app==0.14"
pip install sphinx sphinx-rtd-theme mock

# make sure libspatialindex is available
# This is commented out because spatialindex
# is already available on our mac CI machine
#
# mkdir $VENV_DIR/spatialindex_build
# pushd $VENV_DIR/spatialindex_build > /dev/null
# curl -O http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.bz2
# tar xf spatialindex-src-1.8.5.tar.bz2
# pushd spatialindex-src-1.8.5 > /dev/null
# ./configure --prefix=`pwd`
# make
# make install
# popd > /dev/null
# popd > /dev/null
# export DYLD_LIBRARY_PATH=$VENV_DIR/spatialindex_build/lib:$DYLD_LIBRARY_PATH

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
dist/FSLeyes.app/Contents/MacOS/fsleyes render -vl 8 6 6  -of file.png -sz 572 386 -hc -hl tests/testdata/3d
python tests/compare_images.py file.png tests/testdata/test_screenshot_ortho.png 1000 || true

deactivate
rm -r fsleyes-venv
