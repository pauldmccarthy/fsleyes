#!/usr/bin/env python
#
# test_overlay_vector_orient.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op
import shutil

import pytest

import fsl.data.image as fslimage

from fsleyes.tests import run_cli_tests, fliporient


pytestmark = pytest.mark.overlayclitest


cli_tests = """
          dti/dti_V1.nii.gz                   -ot linevector     # Should display correctly
          dti/dti_V1.nii.gz                   -ot linevector -of # Should display incorrectly (vectors L/R flipped)
          {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector     # Should display correctly
          {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector -of # Should display incorrectly (vectors L/R flipped)
-ds world dti/dti_V1.nii.gz                   -ot linevector     # Should display correctly
-ds world dti/dti_V1.nii.gz                   -ot linevector -of # Should display incorrectly (vectors L/R flipped)
-ds world {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector     # Should display correctly
-ds world {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector -of # Should display incorrectly (vectors L/R flipped)

          dti/               -ot tensor                   # Should display correctly
          dti/               -ot tensor    -of            # Should display incorrectly (vectors L/R flipped)
          {{flipdir('dti')}} -ot tensor     # Should display correctly
          {{flipdir('dti')}} -ot tensor -of # Should display incorrectly (vectors L/R flipped)
-ds world dti                -ot tensor     # Should display correctly
-ds world dti                -ot tensor -of # Should display incorrectly (vectors L/R flipped)
-ds world {{flipdir('dti')}} -ot tensor     # Should display correctly
-ds world {{flipdir('dti')}} -ot tensor -of # Should display incorrectly (vectors L/R flipped)

          sh                   -ot sh     # Should display correctly
          sh                   -ot sh -of # Should display incorrectly (vectors L/R flipped)
          {{fliporient('sh')}} -ot sh     # Should display correctly
          {{fliporient('sh')}} -ot sh -of # Should display incorrectly (vectors L/R flipped)
-ds world sh                   -ot sh     # Should display correctly
-ds world sh                   -ot sh -of # Should display incorrectly (vectors L/R flipped)
-ds world {{fliporient('sh')}} -ot sh     # Should display correctly
-ds world {{fliporient('sh')}} -ot sh -of # Should display incorrectly (vectors L/R flipped)
"""


def flipdir(dirname):
    newdir = '{}_flipdir'.format(dirname.strip(op.sep))

    if op.exists(newdir):
        return newdir

    os.mkdir(newdir)
    for f in os.listdir(dirname):
        if not op.exists(op.join(dirname, f)):
            continue
        if not fslimage.looksLikeImage(f):
            continue
        flipped = fliporient(op.join(dirname, f))
        flipped = fslimage.addExt(flipped)
        shutil.move(flipped, op.join(newdir, f))

    return newdir


def test_overlay_vector_orient():
    extras = {
        'fliporient' : fliporient,
        'flipdir'    : flipdir,
    }
    run_cli_tests('test_overlay_vector_orient', cli_tests, extras=extras)
