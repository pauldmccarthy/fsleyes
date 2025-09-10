#!/bin/bash

thisdir=$(cd $(dirname $0) && pwd)

pip install .
pip install requests jinja2

name=$1
zenodo_url=$2
zenodo_tkn=$3
zenodo_depid=$4

version=$(python -c "import fsleyes.version as v; print(v.__version__)")
upfile=`pwd`/dist/"$name"-"$version".tar.gz
metafile=`pwd`/.ci/zenodo_meta.json.jinja2
date=`date +"%Y-%m-%d"`

python "$thisdir"/zenodo.py \
       "$zenodo_url" \
       "$zenodo_tkn" \
       "$zenodo_depid" \
       "$upfile" \
       "$metafile" \
       "$version" \
       "$date"
