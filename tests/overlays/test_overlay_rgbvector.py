#!/usr/bin/env python
#
# test_overlay_rgbvector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from .. import run_cli_tests, asrgb


pytestmark = pytest.mark.overlayclitest


cli_tests = """
dti/dti_V1 -ot rgbvector
dti/dti_V1 -ot rgbvector -in none
dti/dti_V1 -ot rgbvector -in linear
dti/dti_V1 -ot rgbvector -in spline

dti/dti_V1 -ot rgbvector            -b 75 -c 75
dti/dti_V1 -ot rgbvector -in none   -b 75 -c 75
dti/dti_V1 -ot rgbvector -in linear -b 75 -c 75
dti/dti_V1 -ot rgbvector -in spline -b 75 -c 75
dti/dti_V1 -ot rgbvector            -b 25 -c 25
dti/dti_V1 -ot rgbvector -in none   -b 25 -c 25
dti/dti_V1 -ot rgbvector -in linear -b 25 -c 25
dti/dti_V1 -ot rgbvector -in spline -b 25 -c 25

{{asrgb('dti/dti_V1')}} -ot rgbvector
"""

def test_overlay_rgbvector():
    extras = {
        'asrgb' : asrgb,
    }
    run_cli_tests('test_overlay_rgbvector', cli_tests, extras=extras)
