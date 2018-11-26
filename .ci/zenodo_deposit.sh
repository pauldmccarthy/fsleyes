#!/bin/bash

tmp=`dirname $0`
pushd $tmp > /dev/null
thisdir=`pwd`
popd > /dev/null

zenodo_url=$1
zenodo_tkn=$2
zenodo_depid=$3

version=`python setup.py -V`
upfile=`pwd`/dist/fslpy-"$version".tar.gz
metafile=`pwd`/.ci/zenodo_meta.json.jinja2
date=`date +"%Y-%m-%d"`

pip install --retries 10 requests jinja2

python "$thisdir"/zenodo.py \
       "$zenodo_url" \
       "$zenodo_tkn" \
       "$zenodo_depid" \
       "$upfile" \
       "$metafile" \
       "$version" \
       "$date"
