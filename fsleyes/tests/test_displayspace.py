#!/usr/bin/env python
#
# test_displayspace.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests, resampled, roi, rotate, swapdim


pytestmark = pytest.mark.clitest


tests = """
                -vl 10 8 8 -o 0 3d           {{roi('3d', (8, 13, 6, 10, 6, 10))}}       -cm red-yellow
                -vl 10 8 8 -o 0 3d {{resampled(roi('3d', (8, 13, 6, 10, 6, 10)), 0.5)}} -cm red-yellow
-ds scaledVoxel -vl 0 0 0  -o 0 3d           {{roi('3d', (8, 13, 6, 10, 6, 10))}}       -cm red-yellow
-ds scaledVoxel -vl 0 0 0  -o 0 3d {{resampled(roi('3d', (8, 13, 6, 10, 6, 10)), 0.5)}} -cm red-yellow

                        3d {{rotate('3d', 20, 20, 20)}} -cm red-yellow -a 50
-ds 3d                  3d {{rotate('3d', 20, 20, 20)}} -cm red-yellow -a 50
-ds 3d_rotated_20_20_20 3d {{rotate('3d', 20, 20, 20)}} -cm red-yellow -a 50
-ds world               3d {{rotate('3d', 20, 20, 20)}} -cm red-yellow -a 50
-ds scaledVoxel         3d {{rotate('3d', 20, 20, 20)}} -cm red-yellow -a 50

-ds 3d                  3d {{swapdim('3d', '-x', 'y', 'z')}}                 -cm red-yellow -a 50
-ds 3d_swapdim_-x_y_z   3d {{swapdim('3d', '-x', 'y', 'z')}}                 -cm red-yellow -a 50
-ds scaledVoxel         3d {{swapdim('3d', '-x', 'y', 'z')}}                 -cm red-yellow -a 50
-ds world               3d {{swapdim('3d', '-x', 'y', 'z')}}                 -cm red-yellow -a 50

-ds 3d                              3d {{resampled(swapdim('3d', '-x', 'y', 'z'), 0.5)}} -cm red-yellow -a 50
-ds 3d_swapdim_-x_y_z_resampled_0.5 3d {{resampled(swapdim('3d', '-x', 'y', 'z'), 0.5)}} -cm red-yellow -a 50
-ds scaledVoxel                     3d {{resampled(swapdim('3d', '-x', 'y', 'z'), 0.5)}} -cm red-yellow -a 50
-ds world                           3d {{resampled(swapdim('3d', '-x', 'y', 'z'), 0.5)}} -cm red-yellow -a 50
"""


def test_displayspace():
    extras = {
        'roi'       : roi,
        'resampled' : resampled,
        'rotate'    : rotate,
        'swapdim'   : swapdim
    }
    run_cli_tests('test_displayspace', tests, extras=extras)
