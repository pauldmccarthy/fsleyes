#!/usr/bin/env python
#
# test_overlay_nifti2d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from . import run_cli_tests, roi


pytestmark = pytest.mark.clitest


cli_tests = """
# planes
{{roi('3d.nii.gz', (0, 17, 0, 14, 7,  8))}}
{{roi('3d.nii.gz', (0, 17, 7,  8, 0, 14))}}
{{roi('3d.nii.gz', (9, 10, 0, 14, 0, 14))}}

# vectors
{{roi('3d.nii.gz', (0, 17, 7,  8, 7,  8))}}
{{roi('3d.nii.gz', (9, 10, 0, 14, 7,  8))}}
{{roi('3d.nii.gz', (9, 10, 7,  8, 0, 14))}}

# onevox
{{roi('3d.nii.gz', (9, 10, 7, 8, 7, 8))}} -or 6980 7000
"""


def test_overlay_nifti2d():
    extras = {
        'roi' : roi,
    }
    run_cli_tests('test_overlay_nifti2d', cli_tests, extras=extras)
