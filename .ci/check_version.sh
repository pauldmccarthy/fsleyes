#!/bin/bash

set -e


source /test.venv/bin/activate
pip install  dist/*.whl

exp=${CI_COMMIT_REF_NAME}
got=$(python -c "import fsleyes.version as v;print(v.__version__)")

echo "Tagged version:           ${exp}"
echo "Reported FSLeyes version: ${got}"

if [[ ${exp} == ${got} ]]; then
  exit 0
else
  exit 1
fi
