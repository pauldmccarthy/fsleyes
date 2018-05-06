#!/usr/bin/env python
#
# test_overlay_linevector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest
import fsl.data.image as fslimage

from . import run_cli_tests


pytestmark = pytest.mark.overlaytest


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

# Test 1D/2D  vector images
{{roi('dti/dti_V1', (0, 8, 4, 5, 4, 5))}} -ot linevector
{{roi('dti/dti_V1', (0, 8, 0, 8, 4, 5))}} -ot linevector
"""

def roi(fname, roi):
    base    = fslimage.removeExt(fname)
    outfile = '{}_roi_{}_{}_{}_{}_{}_{}'.format(base, *roi)

    img = fslimage.Image(fname)
    xs, xe, ys, ye, zs, ze = roi
    data = img[xs:xe, ys:ye, zs:ze, ...]
    img = fslimage.Image(data, header=img.header)

    img.save(outfile)

    return outfile


def test_overlay_linevector():
    extras = {
        'roi' : roi,
    }
    run_cli_tests('test_overlay_linevector', cli_tests, extras=extras)
