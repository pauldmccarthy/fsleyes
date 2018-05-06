#!/usr/bin/env python
#
# test_overlay_giftimesh.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from . import run_cli_tests


pytestmark = pytest.mark.overlaytest


cli_tests = """
gifti/white.surf.gii -mc 1 0 0
gifti/white.surf.gii -mc 1 0 0 -o
gifti/white.surf.gii -mc 1 0 0    -w 1
gifti/white.surf.gii -mc 1 0 0    -w 5
gifti/white.surf.gii -mc 1 0 0    -w 10
gifti/white.surf.gii -mc 1 0 0 -o -w 1
gifti/white.surf.gii -mc 1 0 0 -o -w 5
gifti/white.surf.gii -mc 1 0 0 -o -w 10
gifti/white.surf.gii -mc 1 0 0 -o -w 10 -cm hot -vd gifti/data3d.txt
gifti/white.surf.gii -mc 1 0 0 -o -w 10 -cm hot -vd gifti/data4d.txt
gifti/white.surf.gii -mc 1 0 0 -o -w 10 -cm hot -vd gifti/data4d.txt -vdi 3
"""

def test_overlay_giftimesh():
    extras = {}
    run_cli_tests('test_overlay_giftimesh', cli_tests, extras=extras)
