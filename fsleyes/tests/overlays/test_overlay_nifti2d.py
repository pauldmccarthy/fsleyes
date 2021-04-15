#!/usr/bin/env python
#
# test_overlay_nifti2d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from fsleyes.tests import run_cli_tests, roi, asrgb


pytestmark = pytest.mark.overlayclitest


cli_tests = """
# volume
# planes
{{roi('3d', (0, 17, 0, 14, 7,  8))}}
{{roi('3d', (0, 17, 7,  8, 0, 14))}}
{{roi('3d', (9, 10, 0, 14, 0, 14))}}

# vectors
{{roi('3d', (0, 17, 7,  8, 7,  8))}}
{{roi('3d', (9, 10, 0, 14, 7,  8))}}
{{roi('3d', (9, 10, 7,  8, 0, 14))}}

# onevox
{{roi('3d', (9, 10, 7, 8, 7, 8))}} -or 6980 7000

# dti/4D
# planes
{{roi('dti/dti_V1', (0, 8, 0, 8, 4, 5))}}
{{roi('dti/dti_V1', (0, 8, 4, 5, 0, 8))}}
{{roi('dti/dti_V1', (4, 5, 0, 8, 0, 8))}}
{{roi('dti/dti_V1', (0, 8, 0, 8, 4, 5))}} -ot rgbvector
{{roi('dti/dti_V1', (0, 8, 4, 5, 0, 8))}} -ot rgbvector
{{roi('dti/dti_V1', (4, 5, 0, 8, 0, 8))}} -ot rgbvector
{{roi('dti/dti_V1', (0, 8, 0, 8, 4, 5))}} -ot linevector
{{roi('dti/dti_V1', (0, 8, 4, 5, 0, 8))}} -ot linevector
{{roi('dti/dti_V1', (4, 5, 0, 8, 0, 8))}} -ot linevector

# vectors
{{roi('dti/dti_V1', (0, 8, 4, 5, 4, 5))}}
{{roi('dti/dti_V1', (4, 5, 0, 8, 4, 5))}}
{{roi('dti/dti_V1', (4, 5, 4, 5, 0, 8))}}
{{roi('dti/dti_V1', (0, 8, 4, 5, 4, 5))}} -ot rgbvector
{{roi('dti/dti_V1', (4, 5, 0, 8, 4, 5))}} -ot rgbvector
{{roi('dti/dti_V1', (4, 5, 4, 5, 0, 8))}} -ot rgbvector
{{roi('dti/dti_V1', (0, 8, 4, 5, 4, 5))}} -ot linevector
{{roi('dti/dti_V1', (4, 5, 0, 8, 4, 5))}} -ot linevector
{{roi('dti/dti_V1', (4, 5, 4, 5, 0, 8))}} -ot linevector

# onevox
{{roi('dti/dti_V1', (4, 5, 4, 5, 4, 5))}} -or -1 0
{{roi('dti/dti_V1', (4, 5, 4, 5, 4, 5))}} -ot rgbvector
{{roi('dti/dti_V1', (4, 5, 4, 5, 4, 5))}} -ot linevector

# rgb image
# planes
{{asrgb(roi('dti/dti_V1', (0, 8, 0, 8, 4, 5)))}}
{{asrgb(roi('dti/dti_V1', (0, 8, 4, 5, 0, 8)))}}
{{asrgb(roi('dti/dti_V1', (4, 5, 0, 8, 0, 8)))}}
{{asrgb(roi('dti/dti_V1', (0, 8, 0, 8, 4, 5)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (0, 8, 4, 5, 0, 8)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (4, 5, 0, 8, 0, 8)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (0, 8, 0, 8, 4, 5)))}} -ot linevector
{{asrgb(roi('dti/dti_V1', (0, 8, 4, 5, 0, 8)))}} -ot linevector
{{asrgb(roi('dti/dti_V1', (4, 5, 0, 8, 0, 8)))}} -ot linevector

# vectors
{{asrgb(roi('dti/dti_V1', (0, 8, 4, 5, 4, 5)))}}
{{asrgb(roi('dti/dti_V1', (4, 5, 0, 8, 4, 5)))}}
{{asrgb(roi('dti/dti_V1', (4, 5, 4, 5, 0, 8)))}}
{{asrgb(roi('dti/dti_V1', (0, 8, 4, 5, 4, 5)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (4, 5, 0, 8, 4, 5)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (4, 5, 4, 5, 0, 8)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (0, 8, 4, 5, 4, 5)))}} -ot linevector
{{asrgb(roi('dti/dti_V1', (4, 5, 0, 8, 4, 5)))}} -ot linevector
{{asrgb(roi('dti/dti_V1', (4, 5, 4, 5, 0, 8)))}} -ot linevector

# onevox
{{asrgb(roi('dti/dti_V1', (4, 5, 4, 5, 4, 5)))}} -or 0 20
{{asrgb(roi('dti/dti_V1', (4, 5, 4, 5, 4, 5)))}} -ot rgbvector
{{asrgb(roi('dti/dti_V1', (4, 5, 4, 5, 4, 5)))}} -ot linevector
"""


def test_overlay_nifti2d():
    extras = {
        'roi'   : roi,
        'asrgb' : asrgb
    }
    run_cli_tests('test_overlay_nifti2d', cli_tests, extras=extras)
