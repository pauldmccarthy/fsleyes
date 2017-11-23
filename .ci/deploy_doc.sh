#!/bin/bash

set -e

rsync -rv userdoc/"$CI_COMMIT_REF_NAME" "userdocdeploy:"
rsync -rv apidoc/"$CI_COMMIT_REF_NAME" "apidocdeploy:"
