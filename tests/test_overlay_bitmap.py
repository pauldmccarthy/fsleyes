#!/usr/bin/env python
#
# test_overlay_bitmap.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import shutil
import os.path as op

import pytest

from . import run_cli_tests


pytestmark = pytest.mark.overlayclitest


cli_tests = """
-xh -yh {{splash()}}
-xh -yh {{splash()}} -ot rgb
"""


def splash():
    testdir   = op.dirname(__file__)
    splashimg = op.join(testdir, '..', 'assets', 'icons', 'splash', 'splash.png')
    shutil.copy(splashimg, '.')
    return 'splash.png'


def test_overlay_bitmap():
    extras = {'splash' : splash}
    run_cli_tests('test_overlay_bitmap', cli_tests, extras=extras)
