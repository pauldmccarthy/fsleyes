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
                   libxtst-dev

source /test.venv/bin/activate
pip install requests numpy six Pillow

mkdir $VIRTUAL_ENV/wx-build
pushd $VIRTUAL_ENV/wx-build > /dev/null

git clone https://github.com/wxWidgets/Phoenix.git
pushd Phoenix > /dev/null
git checkout $WXPYTHON_VERSION
git submodule update --init --recursive

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

# As of wxPython 4.0.0, build.py forces the
# use of C++11, even though none of the
# wxwidgets/phoenix uses any C++ features.
sed -ie "s/'-std=c++11'/''/g" build.py

# python setup.py install will attempt
# to re-run the build we are about to
# do manually, so we need to patch
# setup.py
sed -ie "s/'install' *: wx_install/'install' : orig_install/g" setup.py

# do the build
python ./build.py dox etg --nodoc sip build --release --gtk3

python setup.py install --skip-build

# sometimes we get files which are rw-------
chmod -R a+rx $VIRTUAL_ENV/lib/

popd > /dev/null
popd > /dev/null
