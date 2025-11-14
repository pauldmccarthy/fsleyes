#!/bin/bash

set -e

MMDIR=${MAMBA_ROOT_PREFIX}

MMURL=https://micro.mamba.pm/api/micromamba/linux-64/latest
mkdir ${MMDIR}
cd ${MMDIR}
curl -Ls ${MMURL} | tar -xvj bin/micromamba
mmbin=${MMDIR}/bin/micromamba

eval "$(${mmbin} shell hook --shell posix)"

micromamba create -y \
  -c conda-forge \
  -p /test.env \
  "python=${PYTHON_VERSION}" \
  "wxpython=${WXPYTHON_VERSION}" \
  pip \
  setuptools \
  numpy \
  scipy \
  matplotlib \
  sphinx \
  sphinx-rtd-theme \
  coverage \
  pytest \
  pytest-cov \
  coverage \
  pylint \
  flake8
