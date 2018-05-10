#!/usr/bin/env python
#
# test_overlay_mesh_3d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from . import run_cli_tests


pytestmark = pytest.mark.overlaytest


cli_tests = """
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -wf

-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100 -ic
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100     -dc
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100 -ic -dc
"""



def test_overlay_mesh_3d():
    extras = {
    }
    run_cli_tests('test_overlay_mesh_3d', cli_tests, extras=extras)
