#!/usr/bin/env python
#
# test_overlay_linevector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests, roi, asrgb


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
"""


def test_overlay_linevector():
    extras = {
        'roi'   : roi,
        'asrgb' : asrgb,
    }
    run_cli_tests('test_overlay_linevector',
                  cli_tests,
                  extras=extras,
                  threshold=35)
