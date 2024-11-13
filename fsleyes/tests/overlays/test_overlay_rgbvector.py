#!/usr/bin/env python
#
# test_overlay_rgbvector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock

import pytest

from fsleyes.tests import run_cli_tests, asrgb, mul

import fsleyes.gl.textures.data as texdata

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

# Colour normalisation
{{mul('dti/dti_V1', 0.5)}} -ot rgbvector -nr
{{mul('dti/dti_V1', 0.5)}} -ot rgbvector
{{mul('dti/dti_V1', 2.0)}} -ot rgbvector -nr
{{mul('dti/dti_V1', 2.0)}} -ot rgbvector

# Images with intent code 2003 should be
# automaticallt shown as RGB vectors, so
# there shouldn't be any need to specify
# The overlay type at the command-line.
{{mul('dti/dti_V1', 3.0)}} -in spline -nr
"""

extras = {
    'asrgb' : asrgb,
    'mul'   : mul,
}


def test_overlay_rgbvector():
    run_cli_tests('test_overlay_rgbvector', cli_tests, extras=extras)


def test_overlay_rgbvector_nofloattextures():
    texdata.canUseFloatTextures.invalidate()
    with mock.patch('fsleyes.gl.textures.data.canUseFloatTextures',
                    return_value=(False, None, None)):
        run_cli_tests('test_overlay_rgbvector',
                      cli_tests, extras=extras)
