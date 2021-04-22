#!/usr/bin/env python
#
# test_overlay_bitmap.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import shutil
import os.path as op

import pytest

from fsleyes.tests import run_cli_tests
import fsleyes


pytestmark = pytest.mark.overlayclitest


cli_tests = """
-xh -yh {{splash()}}
-xh -yh {{splash()}} -ot rgb
"""


def splash():
    splashimg = op.join(fsleyes.assetDir, 'icons', 'splash', 'splash.png')
    shutil.copy(splashimg, '.')
    return 'splash.png'


def test_overlay_bitmap():
    extras = {'splash' : splash}
    run_cli_tests('test_overlay_bitmap', cli_tests, extras=extras)
