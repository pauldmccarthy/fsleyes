#!/usr/bin/env python
#
# test_render_lightbox.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests, roi



pytestmark = pytest.mark.clitest


cli_tests = """
-zr 0 1 -zx 0 3d.nii.gz
-zr 0 1 -zx 1 3d.nii.gz
-zr 0 1 -zx 2 3d.nii.gz
-zr 0 1 -zx x 3d.nii.gz
-zr 0 1 -zx y 3d.nii.gz
-zr 0 1 -zx z 3d.nii.gz
-zr 0 1 -zx X 3d.nii.gz
-zr 0 1 -zx Y 3d.nii.gz
-zr 0 1 -zx Z 3d.nii.gz

-zr 0 1 -cb -ls 20 3d.nii.gz

-zr 0 1 -sg     3d.nii.gz
-zr 0 1     -hs 3d.nii.gz
-zr 0 1 -sg -hs 3d.nii.gz

# 3d.nii.gz has
#    pixdim 2mm
#    FOV x=34mm Y=28mm Z=28mm
# -> slice spacing
#   x 0.059
#   y 0.071
#   z 0.071

-zx 0 -zr 0    1    -ss 0.059 3d.nii.gz
-zx 0 -zr 0    1    -ss 0.118 3d.nii.gz
-zx 0 -zr 0    1    -ss 0.176 3d.nii.gz
-zx 0 -zr 0    1    -ss 0.235 3d.nii.gz
-zx 0 -zr 0    0.5  -ss 0.059 3d.nii.gz
-zx 0 -zr 0    0.5  -ss 0.118 3d.nii.gz
-zx 0 -zr 0    0.5  -ss 0.176 3d.nii.gz
-zx 0 -zr 0    0.5  -ss 0.235 3d.nii.gz
-zx 0 -zr 0.25 0.75 -ss 0.059 3d.nii.gz
-zx 0 -zr 0.25 0.75 -ss 0.118 3d.nii.gz
-zx 0 -zr 0.25 0.75 -ss 0.176 3d.nii.gz
-zx 0 -zr 0.25 0.75 -ss 0.235 3d.nii.gz

-zx 1 -zr 0    1    -ss 0.071 3d.nii.gz
-zx 1 -zr 0    1    -ss 0.143 3d.nii.gz
-zx 1 -zr 0    1    -ss 0.214 3d.nii.gz
-zx 1 -zr 0    1    -ss 0.286 3d.nii.gz
-zx 1 -zr 0    0.5  -ss 0.071 3d.nii.gz
-zx 1 -zr 0    0.5  -ss 0.143 3d.nii.gz
-zx 1 -zr 0    0.5  -ss 0.214 3d.nii.gz
-zx 1 -zr 0    0.5  -ss 0.286 3d.nii.gz
-zx 1 -zr 0.25 0.75 -ss 0.071 3d.nii.gz
-zx 1 -zr 0.25 0.75 -ss 0.143 3d.nii.gz
-zx 1 -zr 0.25 0.75 -ss 0.214 3d.nii.gz
-zx 1 -zr 0.25 0.75 -ss 0.286 3d.nii.gz

-zx 2 -zr 0    1    -ss 0.071 3d.nii.gz
-zx 2 -zr 0    1    -ss 0.143 3d.nii.gz
-zx 2 -zr 0    1    -ss 0.214 3d.nii.gz
-zx 2 -zr 0    1    -ss 0.286 3d.nii.gz
-zx 2 -zr 0    0.5  -ss 0.071 3d.nii.gz
-zx 2 -zr 0    0.5  -ss 0.143 3d.nii.gz
-zx 2 -zr 0    0.5  -ss 0.214 3d.nii.gz
-zx 2 -zr 0    0.5  -ss 0.286 3d.nii.gz
-zx 2 -zr 0.25 0.75 -ss 0.071 3d.nii.gz
-zx 2 -zr 0.25 0.75 -ss 0.143 3d.nii.gz
-zx 2 -zr 0.25 0.75 -ss 0.214 3d.nii.gz
-zx 2 -zr 0.25 0.75 -ss 0.286 3d.nii.gz

-zr 0 1 -nr 1                 3d.nii.gz
-zr 0 1 -nr 2                 3d.nii.gz
-zr 0 1 -nr 3                 3d.nii.gz
-zr 0 1       -nc 1           3d.nii.gz
-zr 0 1       -nc 2           3d.nii.gz
-zr 0 1       -nc 3           3d.nii.gz
-zr 0 1 -nr 1 -nc 1           3d.nii.gz
-zr 0 1 -nr 1 -nc 2           3d.nii.gz
-zr 0 1 -nr 1 -nc 3           3d.nii.gz
-zr 0 1 -nr 1 -nc 1 -ss 0.143 3d.nii.gz
-zr 0 1 -nr 1 -nc 2 -ss 0.143 3d.nii.gz
-zr 0 1 -nr 1 -nc 3 -ss 0.143 3d.nii.gz

# cursor width
-zr 0 1 -cw 5  3d
-zr 0 1 -cw 10 3d

# fsl/fsleyes/fsleyes!333
# L/R flip for neuro-orientation option in lightbox view was being applied
# around the centre of each overlay's FOV, rather than around the centre of
# the display coordinate system
-zr 0 1     3d -cm blue-lightblue {{roi('3d', (0, 6, 0, 14, 0, 14))}}
-zr 0 1 -no 3d -cm blue-lightblue {{roi('3d', (0, 6, 0, 14, 0, 14))}}

-zx 1 -zr 0 1 -no 3d
-zx 1 -zr 0 1     3d
-zx 2 -zr 0 1 -no 3d
-zx 2 -zr 0 1     3d
"""


def test_render_lightbox():
    extras = {
        'roi' : roi
    }
    run_cli_tests('test_render_lightbox', cli_tests, extras=extras,
                  scene='lightbox')
