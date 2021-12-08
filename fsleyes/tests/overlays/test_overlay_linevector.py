#!/usr/bin/env python
#
# test_overlay_linevector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock

import pytest

import fsleyes.gl.textures.data as texdata

from fsleyes.tests import run_cli_tests, roi, asrgb, mul


pytestmark = pytest.mark.overlayclitest


cli_tests = """
# Test line width
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -lw 1
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -lw 5
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -lw 10

# Test line length scaling
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -nu
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector     -ls  500
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -nu -ls  500
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector     -ls  500 -lw 5
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -nu -ls  500 -lw 5

# Test directed vectors
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -ld
dti/dti_FA.nii.gz dti/dti_V1.nii.gz -ot linevector -ld -ls 500 -lw 3

# test RGB images
dti/dti_FA.nii.gz {{asrgb('dti/dti_V1.nii.gz')}} -ot linevector

# test anisotropic voxels
dti/anisotropic/dti_FA dti/anisotropic/dti_V1 -ot linevector

# unit length / colour scaling
dti/dti_FA.nii.gz        dti/dti_V1.nii.gz          -ot linevector -nu
dti/dti_FA.nii.gz {{mul('dti/dti_V1.nii.gz', 0.5)}} -ot linevector
dti/dti_FA.nii.gz {{mul('dti/dti_V1.nii.gz', 0.5)}} -ot linevector -nu
dti/dti_FA.nii.gz {{mul('dti/dti_V1.nii.gz', 2.0)}} -ot linevector
dti/dti_FA.nii.gz {{mul('dti/dti_V1.nii.gz', 2.0)}} -ot linevector -nu
"""

extras = {
    'roi': roi,
    'asrgb': asrgb,
    'mul': mul,
}


def test_overlay_linevector():
    run_cli_tests('test_overlay_linevector',
                  cli_tests,
                  extras=extras)


import fsleyes.gl.textures.data as d
def test_overlay_linevector_nofloattextures():
    texdata.canUseFloatTextures.invalidate()
    with mock.patch('fsleyes.gl.textures.data.canUseFloatTextures',
                    return_value=(False, None, None)):
        run_cli_tests('test_overlay_linevector_nofloattextures',
                      cli_tests,
                      extras=extras)
