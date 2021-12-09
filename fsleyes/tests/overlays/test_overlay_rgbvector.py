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

# unit length scaling
{{mul('dti/dti_V1', 0.5)}} -ot rgbvector -u
{{mul('dti/dti_V1', 0.5)}} -ot rgbvector
{{mul('dti/dti_V1', 2.0)}} -ot rgbvector -u
{{mul('dti/dti_V1', 2.0)}} -ot rgbvector
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
        run_cli_tests('test_overlay_rgbvector_nofloattextures',
                      cli_tests, extras=extras)
