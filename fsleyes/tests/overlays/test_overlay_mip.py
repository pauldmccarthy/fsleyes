#!/usr/bin/env python
#
# test_overlay_mip.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from fsleyes.tests import run_cli_tests, zero_centre, haveGL21


pytestmark = pytest.mark.overlayclitest


cli_tests = """
               3d.nii.gz     -ot mip
               4d.nii.gz     -ot mip
               3d.nii.gz     -ot mip -in linear
               3d.nii.gz     -ot mip -in spline
{{zero_centre('3d.nii.gz')}} -ot mip -m
{{zero_centre('3d.nii.gz')}} -ot mip -ab
               3d.nii.gz     -ot mip -cm hot
               3d.nii.gz     -ot mip -ll -cr 4000 6000
               3d.nii.gz     -ot mip -w 1
               3d.nii.gz     -ot mip -w 50
               3d.nii.gz     -ot mip -w 100
"""


@pytest.mark.skipif('not haveGL21()')
def test_overlay_mip():

    extras = {'zero_centre' : zero_centre}

    run_cli_tests('test_overlay_mip', cli_tests, extras=extras)
