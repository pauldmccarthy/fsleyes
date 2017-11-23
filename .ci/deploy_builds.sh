#!/bin/bash

set -e

rsync -rv dist/FSLeyes*tar.gz "builddeploy:"
