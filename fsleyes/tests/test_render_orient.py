#!/usr/bin/env python
#
# test_render_3d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import pytest

import nibabel as nib

import fsl.data.image as fslimage

from fsleyes.tests import run_cli_tests, fliporient, rotate


pytestmark = pytest.mark.clitest


# 3d has radio storage order
cli_tests = """
              {{fliporient('3d.nii.gz')}} # Should display in radiological orientation
              3d.nii.gz                   # Should display in radiological orientation
-no           {{fliporient('3d.nii.gz')}} # Should display in neurological orientation
-no           3d.nii.gz                   # Should display in neurological orientation
-no -ds world {{fliporient('3d.nii.gz')}} # Should display in neurological orientation
-no -ds world 3d.nii.gz                   # Should display in neurological orientation
    -ds world {{fliporient('3d.nii.gz')}} # Should display in radiological orientation
    -ds world 3d.nii.gz                   # Should display in radiological orientation

                                    {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in radiological orientation
    -ds world                       {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in radiological orientation
    -ds {{fliporient('3d.nii.gz')}} {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in radiological orientation
    -ds 3d.nii.gz                   {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in radiological orientation
-no                                 {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in neurological orientation
-no -ds world                       {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in neurological orientation
-no -ds {{fliporient('3d.nii.gz')}} {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in neurological orientation
-no -ds 3d.nii.gz                   {{fliporient('3d.nii.gz')}} -cm red 3d.nii.gz -cm blue -a 75 # Should display in neurological orientation

-xz 1500 -yz 1500 -zz 1500                                             {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in radiological orientation
-xz 1500 -yz 1500 -zz 1500     -ds world                               {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in radiological orientation
-xz 1500 -yz 1500 -zz 1500     -ds {{fliporient('dti/dti_V1.nii.gz')}} {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in radiological orientation
-xz 1500 -yz 1500 -zz 1500     -ds dti/dti_V1.nii.gz                   {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in radiological orientation
-xz 1500 -yz 1500 -zz 1500 -no                                         {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in neurological orientation
-xz 1500 -yz 1500 -zz 1500 -no -ds world                               {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in neurological orientation
-xz 1500 -yz 1500 -zz 1500 -no -ds {{fliporient('dti/dti_V1.nii.gz')}} {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in neurological orientation
-xz 1500 -yz 1500 -zz 1500 -no -ds dti/dti_V1.nii.gz                   {{fliporient('dti/dti_V1.nii.gz')}} -ot linevector dti/dti_V1.nii.gz -ot linevector # Should display in neurological orientation

{{sqformcodes('3d.nii.gz', 4, 0)}}  # Labels should be displayed
{{sqformcodes('3d.nii.gz', 0, 4)}}  # Labels should be displayed
{{sqformcodes('3d.nii.gz', 0, 0)}}  # Labels should be unknown

          {{rotate('3d.nii.gz', 30, 30, 30)}} # Labels should be correct!
-ds world {{rotate('3d.nii.gz', 30, 30, 30)}} # Labels should be correct!
"""


def sqformcodes(infile, sform, qform):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_sqformcodes_{}_{}.nii.gz'.format(basename, sform, qform)
    img      = nib.load(infile)
    xform    = img.affine

    img.set_sform(xform, sform)
    img.set_qform(xform, qform)
    img.update_header()

    nib.save(img, outfile)

    return outfile


def test_render_orient():
    extras = {
        'fliporient'  : fliporient,
        'rotate'      : rotate,
        'sqformcodes' : sqformcodes
    }
    run_cli_tests('test_render_orient', cli_tests, extras=extras)
