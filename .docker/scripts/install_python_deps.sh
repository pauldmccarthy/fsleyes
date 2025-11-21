#!/bin/bash

set -e

MMDIR=${MAMBA_ROOT_PREFIX}

if [[ $(uname -a) == *x86_64* ]]; then
  MMURL=https://micro.mamba.pm/api/micromamba/linux-64/latest
elif  [[ $(uname -a) == *aarch64* ]]; then
  MMURL=https://micro.mamba.pm/api/micromamba/linux-aarch64/latest
else
  echo "unknown platform"
  exit 1
fi


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
  dcm2niix \
  flake8
