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
available version. If you have a recent version of FSL, try running
``update_fsl_release`. If this command is not available, or prints an error,
just delete and re-install FSL following the instructions in the `FSL
documentation <https://fsl.fmrib.ox.ac.uk/fsl/docs/#/install/index>`_.



FSL 6.0.7 or newer
^^^^^^^^^^^^^^^^^^

If you have FSL 6.0.7 or newer, you can update to the latest version of FSLeyes
by running the following command::

    update_fsl_package fsleyes

.. note:: If you have trouble running the ``update_fsl_package`` command, try
          updating FSL first using the ``update_fsl_release`` command, or
          just deleting your FSL installation and reinstalling the latest
          version.


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
             packages using your OS package manager. The steps below are
             **suggestions** - you will probably need to adapt them to suit
             your OS and environment.


FSLeyes is available on `PyPi <https://pypi.org/project/fsleyes/>`_, and
should work with Python 3.9 and newer. The best way to install FSLeyes from
PyPi is to create an isolated `virtual environment
<https://docs.python.org/3/library/venv.html>`_, and install FSLeyes into it.


.. note:: As an alternative to creating and managing your virtual environments
          by hand, there are many tools which can be used to manage Python
          environments, including `pixi <https://pixi.sh/latest/>`_, `uv
          <https://docs.astral.sh/uv/>`_, `hatch <https://hatch.pypa.io/>`_,
          and `poetry <https://python-poetry.org/>`_ to name a few.


macOS users
^^^^^^^^^^^

Before installing FSLeyes, you first need to install Python. On macOS, you can
do this in a number of ways, including:

 - Using an official Python installer from https://www.python.org/
 - Installing the XCode Command-Line Tools, by running ``xcode-select --install``
   in a terminal.
 - Installing `Anaconda <https://www.anaconda.com/download>`_ or `Miniconda
   <https://docs.anaconda.com/miniconda/>`_.


Once you have installed Python, you can create and activate a virtual
environment for FSLeyes with these commands::

  python -m venv fsleyes-virtualenv
  . ./fsleyes-virtualenv/bin/activate

Then you should be able to install FSLeyes like so::

    pip install fsleyes


Linux users
^^^^^^^^^^^

Before installing FSLeyes, you first need to install Python and the wxPython
runtime dependencies. Under Ubuntu 24.04, you will need to run the following
command::

    sudo apt install python3 python3-pip python3-venv \
      curl libegl1 libgl1 libgtk-3-0 libnotify4       \
      libpcre2-32-0 libsdl2-2.0-0 libsm6 libxxf86vm1

Then you need to create and activate a virtual environment, and install
wxPython and FSLeyes into it. For example, you can use these commands to
create and activate a virtual environment::

  python -m venv fsleyes-virtualenv
  . ./fsleyes-virtualenv/bin/activate

The easiest way to install wxPython on Linux is to use the pre-release
wxPython builds available at
https://extras.wxpython.org/wxPython4/extras/linux/, e.g.::

    wxpyurl=https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04
    pip install -f  ${wxpyurl} wxpython

Once you have installed wxPython, you can install FSLeyes::

    pip install fsleyes

You should now be able to run the ``fsleyes`` command.


Install into a Docker/Singularity image
---------------------------------------

FSLeyes can be executed from `Docker <https://docs.docker.com/>`_ or
`Singularity <https://sylabs.io/docs/>`_ containers. Here is an example
``Dockerfile`` file which contains FSLeyes::

  FROM ubuntu:24.04

  ENV MMURL="https://micro.mamba.pm/api/micromamba/linux-64/latest"
  ENV MAMBA_ROOT_PREFIX="/micrommaba"
  ENV DEBIAN_FRONTEND="noninteractive"
  ENV TZ="Europe/London"

  RUN apt update
  RUN apt install -y curl bzip2 tar libgl1 libegl1
  RUN mkdir ${MAMBA_ROOT_PREFIX}
  RUN curl -Ls ${MMURL} | tar -C ${MAMBA_ROOT_PREFIX} -xvj bin/micromamba
  RUN eval "$(micromamba/bin/micromamba shell hook -s posix)"
  RUN micromamba install -y -p ${MAMBA_ROOT_PREFIX} -c conda-forge fsleyes

  CMD [ "/micromamba/bin/fsleyes" ]

And an equivalent Singularity definition file::

  Bootstrap: docker
  From: ubuntu:24.04

  %help
    FSLeyes Singularity image


  %post
    export MMURL=https://micro.mamba.pm/api/micromamba/linux-64/latest
    export MAMBA_ROOT_PREFIX=/micromamba
    export TZ="Europe/London"
    export DEBIAN_FRONTEND="noninteractive"
    apt update
    apt install -y curl bzip2 tar libgl1 libegl1
    mkdir ${MAMBA_ROOT_PREFIX}
    curl -Ls ${MMURL} | tar -C ${MAMBA_ROOT_PREFIX} -xvj bin/micromamba
    eval "$(micromamba/bin/micromamba shell hook -s posix)"
    micromamba install -y -p ${MAMBA_ROOT_PREFIX} -c conda-forge fsleyes


  %runscript
    /micromamba/bin/fsleyes "$@"
