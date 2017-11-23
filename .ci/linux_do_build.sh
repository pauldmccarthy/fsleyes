# Download, compile, and install python
pushd /
wget http://python.org/ftp/python/3.5.3/Python-3.5.3.tar.xz
tar xf Python-3.5.3.tar.xz
cd Python-3.5.3
./configure --prefix=`pwd`/install/ --enable-shared
make
make install
export PATH=`pwd`/install/bin:$PATH
export LD_LIBRARY_PATH=`pwd`/install/lib

# Make  sure that a command called "python" exists
pushd install/bin
if [ ! -f python ]; then
  ln -s python3.5 python;
fi

# get pip
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

# Make sure that a command called "pip" exists
if  [ ! -f pip ]; then
  ln -s pip3.5 pip;
fi
popd
popd

# Installing pyopengl-accelerete the
# standard way doesn't seem to work -
# the numpy module doesn't get installed.
# Force-installing from source works
# though.
pip install numpy
pip install --no-binary ":all:" "pyopengl>=3.1.0,<4.0" "pyopengl-accelerate>=3.1.0,<4.0"

# pre-built binaries for wxpython are available
# for ubuntu, but not for centos, where it needs
# to be compiled from source.
if   [[ -f /etc/lsb-release && `grep "Ubuntu 14" /etc/lsb-release` ]]; then
  pip install --only-binary wxpython -f $WXPYTHON_UBUNTU1404_URL "$WXPYTHON_VERSION";
elif [[ -f /etc/lsb-release && `grep "Ubuntu 16" /etc/lsb-release` ]]; then
  pip install --only-binary wxpython -f $WXPYTHON_UBUNTU1604_URL "$WXPYTHON_VERSION";
else
  pip install --pre "$WXPYTHON_VERSION";
fi

# Everything else can be installed
# in the normal manner
pip install -r requirements.txt
pip install "pyinstaller==3.2.1"

# We also manually install the setup_requires
# packages, otherwise they will be built from
# source distributions
pip install sphinx sphinx-rtd-theme mock
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
