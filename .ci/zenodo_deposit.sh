#!/bin/bash

tmp=`dirname $0`
pushd $tmp > /dev/null
thisdir=`pwd`
popd > /dev/null

name=$1
zenodo_url=$2
zenodo_tkn=$3
zenodo_depid=$4

version=$(cat fsleyes/version.py | grep "__version__ =" | tr -d " '" | cut -d '=' -f 2)
upfile=`pwd`/dist/"$name"-"$version".tar.gz
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
