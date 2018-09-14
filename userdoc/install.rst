Installing FSLeyes
==================


There are several ways to obtain and install FSLeyes.


Install as part of FSL (recommended)
------------------------------------


FSLeyes comes bundled with all versions of FSL from 5.0.10 onwards. So if you
have FSL, you already have FSLeyes.

The version which comes bundled with FSL may be slightly out of date, so you
may wish to update FSLeyes within your FSL installation - keep reading.


Install standalone build (recommended)
--------------------------------------


This is currently the recommended way to install FSLeyes.


If your operating system is supported, the easiest way to run FSLeyes is to
download and install a standalone version from the |fsleyes_homepage| home
page.


If you wish to upgrade your version of FSLeyes which was installed as part of
FSL (*note: you may need to ask your system administrator to do this*):

For macOS::

    cd $FSLDIR/bin/
    sudo mv FSLeyes.app FSLeyes.app_backup
    sudo unzip /path/to/downloaded/FSLeyes_macos_latest.zip


For Linux::

    cd $FSLDIR/bin/
    sudo mv FSLeyes FSLeyes_backup
    sudo unzip /path/to/downloaded/FSLeyes_centos6_latest.zip


If you are installing FSLeyes independently of FSL:

1. Download the ``zip`` or ``tar.gz`` file for your platform.

2. Unzip/untar the downloaded file to a location of your choice.

3. Call FSLeyes like this (you may wish to put the directory containing
   the ``fsleyes`` command on your ``$PATH`` environment variable):

   ======== ==========================================================
   Platform Command to run FSLeyes
   ======== ==========================================================
   Linux    ``/path/to/downloaded/FSLeyes/fsleyes``
   macOS    ``/path/to/downloaded/FSLeyes.app/Contents/MacOS/fsleyes``
   ======== ==========================================================


Install from PyPi (advanced)
----------------------------

FSLeyes is available on `PyPi <https://pypi.org/project/fsleyes/>`_, and
should work with Python 2.7, 3.4, 3.5, and 3.6. The best way to install
FSLeyes from PyPi is to create an isolated python environment with `virtualenv
<https://virtualenv.pypa.io/en/stable/>`_ For example, if you are using python
3.5::

    python -m venv fsleyes-virtualenv
    . fsleyes-virtualenv/bin/activate


macOS users
^^^^^^^^^^^

Once you have activated your virtual environment, you should be able to
install FSLeyes like so::

    pip install fsleyes


Linux users
^^^^^^^^^^^

Before installing FSLeyes, you first need to install wxPython. The easiest way
to do this on Linux is to use the pre-release wxPython builds available at
https://extras.wxpython.org/wxPython4/extras/linux/. For example, if you are
using CentOS 7::

    pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk2/centos-7 wxpython
    pip install fsleyes

You will also need to install the wxPython runtime dependencies. Under CentOS
7, you will need to run the following command::

    sudo yum install freeglut SDL

Similarly, under Ubuntu::

    sudo apt-get install freeglut3 libsdl1.2debian


Another option is to install wxPython directly from PyPi - if you do this, you
will need to have C/C++ compilers installed, and all of the dependencies
required to compile wxPython. Under CentOS 7, run the following commands::

    sudo yum groupinstall "Development tools"
    sudo yum install gtk2-devel gtk3-devel webkitgtk-devel webkitgtk3-devel
    sudo yum install libjpeg-turbo-devel libtiff-devel SDL-devel gstreamer-plugins-base-devel libnotify-devel freeglut-devel

Under Ubuntu, run the following::

    sudo apt-get install build-essential
    sudo apt-get install libgtk2.0-dev libgtk-3-dev libwebkitgtk-dev libwebkitgtk-3.0-dev
    sudo apt-get install libjpeg-turbo8-dev libtiff5-dev libsdl1.2-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libnotify-dev freeglut3-dev

Then you should be able to run ``pip install fsleyes``.


Install from ``conda-forge`` (advanced)
---------------------------------------


FSLeyes will soon be available on conda-forge.
