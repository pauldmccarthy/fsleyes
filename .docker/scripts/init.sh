#!/usr/bin/env bash

eval "$(/mamba/bin/micromamba shell hook --shell posix)"
micromamba activate /test.env

exec -l "$@"
