#!/bin/bash

set -e

apt-get update -y
apt-get install -y graphviz

pip install git+https://github.com/pauldmccarthy/sphinx_rtd_dark_mode.git@bf/fixes
pip install ".[doc]"


reffile=userdoc/command_line_reference.rst

cat << EOF > ${reffile}

FSLeyes command-line reference
------------------------------

Below you will find the full FSLeyes command-line reference - you can view
this locally by running \`\`fsleyes --fullhelp\`\` or \`\`fsleyes -fh\`\`.

::

EOF

fsleyes -fh | sed 's/^/  /g' >> ${reffile}

sphinx-build userdoc public/userdoc
