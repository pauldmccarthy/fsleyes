#!/usr/bin/env bash

export PATH=/dcm2niix:$PATH
eval "$(/mamba/bin/micromamba shell hook --shell posix)"
micromamba activate /test.env

exec -l "$@"
