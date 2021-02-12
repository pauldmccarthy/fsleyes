#!/usr/bin/env python
#
# test_overlay_volume_3d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from .. import run_cli_tests, roi


pytestmark = pytest.mark.overlayclitest


cli_tests = """
-dl 3d
-dl 3d  -in linear
-dl 3d  -in spline

-dl 3d   -ns 5
-dl 3d   -ns 10
-dl 3d   -ns 25
-dl 3d   -ns 100
-dl 3d   -ns 200

-dl 3d   -bf 0.001
-dl 3d   -bf 0.25
-dl 3d   -bf 0.5
-dl 3d   -bf 0.75
-dl 3d   -bf 0.9

-dl 3d   -r 25
-dl 3d   -r 50
-dl 3d   -r 75

-dl 3d   -cp 25 0   0
-dl 3d   -cp 50 0   0
-dl 3d   -cp 75 0   0

-dl 3d   -cp 50  0   0
-dl 3d   -cp 50  0 -90
-dl 3d   -cp 50 90 -90

-dl 3d   -cp 50 0 0 -cp 50  0 -90
-dl 3d   -cp 50 0 0 -cp 50 45 -45
-dl 3d   -cp 50 0 0 -cp 50 45 -45 -cp 50  90 90
-dl 3d   -cp 50 0 0 -cp 50 45 -45 -cp 50 135 45

-dl 3d -s 0
-dl 3d -s 1
-dl 3d -s 3
-dl 3d -s 6

-dl 3d -cp 25 0 0  -cp 50 90 45 -cp 50 90 -45 -m intersection
-dl 3d -cp 75 0 0  -cp 50 90 45 -cp 50 90 -45 -m union
-dl 3d -cp 75 0 0  -cp 50 90 45 -cp 50 90 -45 -m complement

-rot -45 -30 0 {{roi('3d.nii.gz', (0, 17, 0, 14, 6,  7))}} {{roi('3d.nii.gz', (0, 17, 6,  7, 0, 14))}} {{roi('3d.nii.gz', (8,  9, 0, 14, 0, 14))}}
-rot 125 -45 0 {{roi('3d.nii.gz', (0, 17, 0, 14, 6,  7))}} {{roi('3d.nii.gz', (0, 17, 6,  7, 0, 14))}} {{roi('3d.nii.gz', (8,  9, 0, 14, 0, 14))}}
"""



def test_overlay_volume_3d():
    extras = {
        'roi' : roi
    }
    run_cli_tests('test_overlay_volume_3d',
                  cli_tests,
                  extras=extras,
                  scene='3d',
                  threshold=40)
