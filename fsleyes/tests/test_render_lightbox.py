#!/usr/bin/env python
#
# test_render_lightbox.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.clitest


cli_tests = """
-zx 0 3d.nii.gz
-zx 1 3d.nii.gz
-zx 2 3d.nii.gz
-zx x 3d.nii.gz
-zx y 3d.nii.gz
-zx z 3d.nii.gz
-zx X 3d.nii.gz
-zx Y 3d.nii.gz
-zx Z 3d.nii.gz

-cb -ls 20 3d.nii.gz

-sg     3d.nii.gz
    -hs 3d.nii.gz
-sg -hs 3d.nii.gz

-ss 2 3d.nii.gz
-ss 4 3d.nii.gz
-ss 6 3d.nii.gz
-ss 8 3d.nii.gz

# X=34 mm Y=28 mm Z=28 mm
-zx 2        -zr 0 28  3d.nii.gz
-zx 2 -ss 2  -zr 0 28  3d.nii.gz
-zx 2 -ss 4  -zr 0 28  3d.nii.gz
-zx 2 -ss 6  -zr 0 28  3d.nii.gz
-zx 2 -ss 8  -zr 0 28  3d.nii.gz

-zx 2        -zr 14 28 3d.nii.gz
-zx 2 -ss 2  -zr 14 28 3d.nii.gz
-zx 2 -ss 4  -zr 14 28 3d.nii.gz
-zx 2 -ss 6  -zr 14 28 3d.nii.gz
-zx 2 -ss 8  -zr 14 28 3d.nii.gz

-zx 2        -zr 0 14  3d.nii.gz
-zx 2 -ss 2  -zr 0 14  3d.nii.gz
-zx 2 -ss 4  -zr 0 14  3d.nii.gz
-zx 2 -ss 6  -zr 0 14  3d.nii.gz
-zx 2 -ss 8  -zr 0 14  3d.nii.gz

-zx 2        -zr 7 21  3d.nii.gz
-zx 2 -ss 2  -zr 7 21  3d.nii.gz
-zx 2 -ss 4  -zr 7 21  3d.nii.gz
-zx 2 -ss 6  -zr 7 21  3d.nii.gz
-zx 2 -ss 8  -zr 7 21  3d.nii.gz

       -nc  5  3d.nii.gz
-nr  5         3d.nii.gz
-nr 10 -nc  5  3d.nii.gz
-nr  5 -nc 10  3d.nii.gz
-nr 10 -nc 10  3d.nii.gz
"""


def test_render_lightbox():
    extras = {
    }
    run_cli_tests('test_render_lightbox', cli_tests, extras=extras,
                  scene='lightbox')
