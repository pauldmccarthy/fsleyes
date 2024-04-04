#!/bin/bash

set -e

apt-get install -y libgconf2-dev
apt-get install -y dpkg-dev \
                   build-essential \
                   freeglut3-dev \
                   libgl1-mesa-dev \
                   libglu1-mesa-dev \
                   libgstreamer-plugins-base1.0-dev \
                   libgtk-3-dev \
                   libjpeg-dev \
                   libnotify-dev \
                   libpng-dev \
                   libsdl2-dev \
                   libsm-dev \
                   libtiff-dev \
                   libwebkit2gtk-4.0-dev \
                   libxtst-dev \
                   patchelf

$PY_VENV /wxpy-build.env
source /wxpy-build.env/bin/activate

pip install --upgrade pip setuptools wheel

mkdir $VIRTUAL_ENV/wx-build
pushd $VIRTUAL_ENV/wx-build > /dev/null

wget https://pypi.io/packages/source/w/wxPython/wxPython-${WXPYTHON_VERSION}.tar.gz
tar xf wxPython-${WXPYTHON_VERSION}.tar.gz
pushd wxPython-${WXPYTHON_VERSION} > /dev/null

# need newer sip for py312 compat
sed -i "s/sip == 6.7.9/sip == 6.7.11/g" requirements/devel.txt
pip install -r requirements/devel.txt
pip install -r requirements/install.txt

# patch the wxwidgets build opts
configopts="            '--disable-webviewwebkit',
            '--disable-webview',
            '--enable-graphics_ctx',
            '--enable-display',
            '--enable-geometry',
            '--enable-debug_flag',
            '--enable-optimise',
            '--disable-debugreport',
            '--enable-uiactionsim',
            '--enable-autoidman',
            '--with-xtest']"

startline=$(cat buildtools/build_wxwidgets.py | grep -n "wxpy_configure_opts =")
startline=$(echo -n $startline | sed -e 's/^\([0-9]\+\).*$/\1/g')

endline=$(tail -n +"$startline" buildtools/build_wxwidgets.py | grep -n -e "^ *\] *$")
endline=$(echo -n $endline | sed -e 's/^\([0-9]\+\).*$/\1/g')
endline=$(echo "$startline + $endline" | bc)

head -n "$startline" buildtools/build_wxwidgets.py  > tmp
echo "$configopts"                                 >> tmp
tail -n +"$endline" buildtools/build_wxwidgets.py  >> tmp
mv tmp buildtools/build_wxwidgets.py

# Above we add --disable-webview to the
# wxwidgets config opts - we also need to
# prevent the wx.html2 sip wrappers from
# being compiled.
sed -ie "s/^\(.*html2.*\)$/#\1/g" wscript

BUILD_ARGS=("--no_magic" "--release" "--gtk3" "--prefix=/test.venv/" "--jobs=$(nproc)")

# do the build
python ./build.py sip       "${BUILD_ARGS[@]}"
python ./build.py build_wx  "${BUILD_ARGS[@]}"
python ./build.py build_py  "${BUILD_ARGS[@]}"

# install into test venv
deactivate
source /test.venv/bin/activate

python ./build.py install_wx "${BUILD_ARGS[@]}"
python ./build.py install_py "${BUILD_ARGS[@]}"

# sometimes we get files which are rw-------
chmod -R a+rx $VIRTUAL_ENV/lib/

# .so files seem to have trouble finding each other
wxdir=$(cd $VIRTUAL_ENV/lib/python*/site-packages/wx/ && pwd)
for f in $wxdir/*.so; do
  patchelf $f --set-rpath  "$VIRTUAL_ENV/lib/"
done

popd > /dev/null
popd > /dev/null

# sanity check (do this outside of the build dir so python
# doesn't try to import the local <build-dir>/wx/ directory)
python -c "import wx"

rm -rf /wxpy-build.env
