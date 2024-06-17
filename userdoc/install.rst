Installing FSLeyes
==================


There are several ways to obtain and install FSLeyes. FSLeyes comes as a
standard component of an FSL installation, but can also be installed
independently of FSL.


.. note:: The terminal commands in these instructions may require
          administrative privileges, depending on where you have installed
          FSL.  If you encounter permission errors, try repeating the
          command, but prefixing it with `sudo`.


Install as part of FSL (recommended)
------------------------------------


FSLeyes comes bundled with all versions of FSL from 5.0.10 onwards. So if you
have FSL, you already have FSLeyes. The FSLeyes version which comes bundled
with FSL may be slightly out of date, but it is straightforward to update
using ``conda``.

If you have an older version of FSL, it is recommended to update to the latest
available version - you can do this by downloading and running the
`fslinstaller.py` script, available on the `FSL website
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_.


FSL 6.0.7 or newer
^^^^^^^^^^^^^^^^^^

If you have FSL 6.0.7 or newer, you can update to the latest version of FSLeyes
by running the following command::

    update_fsl_package -u fsleyes


FSL 6.0.6 or newer
^^^^^^^^^^^^^^^^^^

If you have FSL 6.0.6 or newer, you can update to the latest version by running
the following command::

    ${FSLDIR}/bin/conda update -p ${FSLDIR} fsleyes


FSL 6.0.2 or newer
^^^^^^^^^^^^^^^^^^


From FSL 6.0.2 onwards, FSLeyes is installed into the ``fslpython`` conda
environment, which is a part of the FSL installation. You can update to the
latest version of FSLeyes by running the following command::

    $FSLDIR/fslpython/bin/conda update -n fslpython -c conda-forge --update-all fsleyes


FSL 6.0.1 or older
^^^^^^^^^^^^^^^^^^


Versions of FSL prior to 6.0.2 come with a standalone version of
FSLeyes. Before updating, you should remove the old standalone version of
FSLeyes. If you are using macOS::

    rm ${FSLDIR}/bin/fsleyes
    rm -r ${FSLDIR}/bin/FSLeyes.app

Or, if you are using Linux::

    rm ${FSLDIR}/bin/fsleyes
    rm -r ${FSLDIR}/bin/FSLeyes

Now you can install FSLeyes with the following command::

    ${FSLDIR}/fslpython/bin/conda install -n fslpython -c conda-forge --update-all fsleyes

When you want to update FSLeyes again in the future, use this command instead::

    ${FSLDIR}/fslpython/bin/conda update -n fslpython -c conda-forge --update-all fsleyes


Install from ``conda-forge`` (recommended)
------------------------------------------


FSLeyes is available on `conda-forge <https://conda-forge.org/>`_ - if you use
an `anaconda <https://www.anaconda.com/>`_ or `miniconda
<https://docs.conda.io/en/latest/miniconda.html>`_ environment, you can
install FSLeyes into it like so::

    conda install -c conda-forge fsleyes


Install from PyPi (advanced)
----------------------------


.. warning:: This is an advanced option, recommended only if you are
             comfortable working with Python environments, and installing
             packages using your OS package manager. The commands below are
             **suggestions** - you will probably need to adapt them to suit
             your OS and environment.


FSLeyes is available on `PyPi <https://pypi.org/project/fsleyes/>`_, and
should work with Python 3.7 and newer. The best way to install FSLeyes from
PyPi is to create an isolated python environment with a `virtual environment
<https://docs.python.org/3/library/venv.html>`_, and install FSLeyes
into it. To get started::

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

    sudo yum install SDL

Similarly, under Ubuntu::

    sudo apt-get install libsdl1.2debian


Another option is to install wxPython directly from PyPi - if you do this, you
will need to have C/C++ compilers installed, and all of the dependencies
required to compile wxPython. Under CentOS 7, run the following commands::

    sudo yum groupinstall "Development tools"
    sudo yum install gtk2-devel gtk3-devel webkitgtk-devel webkitgtk3-devel
    sudo yum install libjpeg-turbo-devel libtiff-devel SDL-devel gstreamer-plugins-base-devel libnotify-devel

Under Ubuntu, run the following::

    sudo apt-get install build-essential
    sudo apt-get install libgtk2.0-dev libgtk-3-dev libwebkitgtk-dev libwebkitgtk-3.0-dev
    sudo apt-get install libjpeg-turbo8-dev libtiff5-dev libsdl1.2-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libnotify-dev

Then you should be able to run ``pip install fsleyes``.


Install into a Singularity image
--------------------------------

FSLeyes can be executed from `Docker <https://docs.docker.com/>`_ or
`Singularity <https://sylabs.io/docs/>`_ containers. Here is an example
Singularity definition file which contains FSLeyes::

    Bootstrap: docker
    From: centos:7

    %help
      FSLeyes Singularity image

    %post
      yum -y update
      yum -y install epel-release
      yum -y install wget mesa-libGL mesa-libOSMesa
      wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      sh Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda3
      /miniconda3/bin/conda create -p /fsleyes-env -c conda-forge fsleyes

    %environment
      source /miniconda3/bin/activate /fsleyes-env

    %runscript
      fsleyes "$@"
