#!/usr/bin/env python
#
# test_overlay_volume_3d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests, roi, haveGL21


pytestmark = pytest.mark.overlayclitest


# we add -in linear to all overlays so we
# get the same results on GL14 and GL21
# (as GL21 defaults to spline, which is
# not available in GL14)
cli_tests = """
-dl 3d -in linear
-dl 3d -in none

-dl 3d -in linear  -ns 5
-dl 3d -in linear  -ns 10
-dl 3d -in linear  -ns 25
-dl 3d -in linear  -ns 100
-dl 3d -in linear  -ns 200

-dl 3d -in linear  -bf 0.001
-dl 3d -in linear  -bf 0.25
-dl 3d -in linear  -bf 0.5
-dl 3d -in linear  -bf 0.9

-dl 3d -in linear  -r 25
-dl 3d -in linear  -r 50
-dl 3d -in linear  -r 75

# blendByIntensity
-dl -rot 30 -30 30 3d -in linear     -ll -dr 4000 8000
-dl -rot 30 -30 30 3d -in linear -bi -ll -dr 4000 8000

# smoothing (only available via CLI)
-dl 3d -in linear -s 0
-dl 3d -in linear -s 1
-dl 3d -in linear -s 3
-dl 3d -in linear -s 6

# clip planes
-dl 3d -in linear -cp 25 0   0
-dl 3d -in linear -cp 50 0   0
-dl 3d -in linear -cp 75 0   0

-dl 3d -in linear -cp 50  0   0
-dl 3d -in linear -cp 50  0 -90
-dl 3d -in linear -cp 50 90 -90

-dl 3d -in linear -cp 50 0 0 -cp 50  0 -90
-dl 3d -in linear -cp 50 0 0 -cp 50 45 -45
-dl 3d -in linear -cp 50 0 0 -cp 50 45 -45 -cp 50  90 90
-dl 3d -in linear -cp 50 0 0 -cp 50 45 -45 -cp 50 135 45

-dl 3d -in linear -cp 25 0 0 -cp 50 90 45 -cp 50 90 -45 -m intersection
-dl 3d -in linear -cp 75 0 0 -cp 50 90 45 -cp 50 90 -45 -m union
-dl 3d -in linear -cp 75 0 0 -cp 50 90 45 -cp 50 90 -45 -m complement
"""

cli_tests_2d =  """
# 2D images
-dl -rot -45 -30 0 {{roi('3d.nii.gz', (0, 17, 0, 14, 6,  7))}} -in linear {{roi('3d.nii.gz', (0, 17, 6,  7, 0, 14))}} -in linear {{roi('3d.nii.gz', (8,  9, 0, 14, 0, 14))}} -in linear
-dl -rot 125 -45 0 {{roi('3d.nii.gz', (0, 17, 0, 14, 6,  7))}} -in linear {{roi('3d.nii.gz', (0, 17, 6,  7, 0, 14))}} -in linear {{roi('3d.nii.gz', (8,  9, 0, 14, 0, 14))}} -in linear
"""


# spline interpolation is only available on GL21
cli_splinterp_test = """
# spline should be default
-dl               3d
-dl               3d -in spline
-dl -rot 30 30 30 3d
-dl -rot 30 30 30 3d -cp 50 90 45
"""


# volume lighting is only available on GL21
cli_lighting_tests = """
3d                        -ns 400
-lp   0 -45 0          3d -ns 400
-lp   0 -90 0          3d -ns 400
-lp  60 -90 0          3d -ns 400
-lp -60 -90 0          3d -ns 400
-lp   0 -90 0  -ld 0.6 3d -ns 400
-lp   0 -90 0          3d -ns 400 -in linear
-lp   0 -90 0          3d -ns 400 -in none
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


# Blending multiple volumes in GL14 doesn't quite work,
# because of limitations in the fragment shader w.r.t.
# calculating fragment depth.
@pytest.mark.skipif('not haveGL21()')
def test_overlay_volume_3d_2d():
    extras = {
        'roi' : roi
    }
    run_cli_tests('test_overlay_volume_3d_2d',
                  cli_tests_2d,
                  extras=extras,
                  scene='3d',
                  threshold=40)


@pytest.mark.skipif('not haveGL21()')
def test_overlay_volume_3d_spline_interp():
    run_cli_tests('test_overlay_volume_3d_spline_interp',
                  cli_splinterp_test,
                  scene='3d',
                  threshold=40)



@pytest.mark.skipif('not haveGL21()')
def test_overlay_volume_3d_lighting():
    run_cli_tests('test_overlay_volume_3d_lighting',
                  cli_lighting_tests,
                  scene='3d',
                  threshold=40)
