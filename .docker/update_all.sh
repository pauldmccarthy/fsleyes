#!/bin/bash

set -e

if [ "$#" -lt "2" ]; then
  echo "Usage: update_all build deploy [docker build args]"
  exit 1
fi

build=$1
deploy=$2
shift
shift
buildopts=$@

thisdir=`dirname $0`
pushd $thisdir > /dev/null
thisdir=`pwd`
popd > /dev/null

targets="
fsleyes-py36-wxpy4-gtk3
fsleyes-py37-wxpy4-gtk3
fsleyes-py38-wxpy4-gtk3
fsleyes-py39-wxpy4-gtk3
"


if [ "$build" == "1" ]; then
  for target in $targets; do

    pushd $thisdir/$target > /dev/null

    echo docker build -t pauldmccarthy/$target $buildopts -f Dockerfile ..
    docker      build -t pauldmccarthy/$target $buildopts -f Dockerfile .. > ../"$target"-build.log
    popd > /dev/null
  done
fi


if [ "$deploy" == "1" ]; then
  for target in $targets; do
    echo docker push pauldmccarthy/$target
    docker      push pauldmccarthy/$target
  done
fi
