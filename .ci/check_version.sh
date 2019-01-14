#!/bin/bash

set -e

cat fsleyes/version.py | egrep "^__version__ += +'$CI_COMMIT_REF_NAME' *$"
