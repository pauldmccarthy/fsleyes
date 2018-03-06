#!/usr/bin/env bash

set -e

name=$1
version=$2

# add any extra channels that are needed
for channel in $CONDA_CHANNELS; do
    conda config  --append channels $channel
done

# make sure to update fundamental
# packages from the default channel
conda update  --yes -c defaults -n base conda
conda install --yes -c defaults -n base setuptools conda-build

# insert project name/version into meta.yaml
echo "{% set name    = '$name' %}"    >  vars.txt
echo "{% set version = '$version' %}" >> vars.txt
cat vars.txt .conda/meta.yaml > tempfile
mv tempfile .conda/meta.yaml
rm vars.txt

mkdir -p dist/conda-bld

conda build --output-folder=dist/conda-bld .conda

# Make sure package is installable
for pyver in 2.7 3.4 3.5 3.6; do
    conda create -y --name "test$pyver" python=$pyver
    source activate test$pyver
    conda install -y -c file://`pwd`/dist/conda-bld $name
    source deactivate
done
