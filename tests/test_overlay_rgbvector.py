#!/usr/bin/env python
#
# test_overlay_rgbvector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import numpy as np

import pytest
import fsl.data.image as fslimage

from . import run_cli_tests


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

{{ndvec('dti/dti_V1', 1)}}        -ot rgbvector
{{ndvec('dti/dti_V1', 2)}}        -ot rgbvector
{{asrgb('dti/dti_V1')}}           -ot rgbvector
{{asrgb(ndvec('dti/dti_V1', 1))}} -ot rgbvector
{{asrgb(ndvec('dti/dti_V1', 2))}} -ot rgbvector
"""

def asrgb(infile):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_asrgb.nii.gz'.format(basename)
    img      = fslimage.Image(infile)
    data     = img.nibImage.get_data()

    shape    = data.shape[:3]
    rgbdtype = np.dtype([('R', 'uint8'), ('G', 'uint8'), ('B', 'uint8')])
    newdata  = np.zeros(shape, dtype=rgbdtype)

    for c, ci in zip('RGB', range(3)):
        cd         = (0.5 * data[..., ci] + 0.5) * 255
        newdata[c] = np.round(cd).astype(np.uint8)

    fslimage.Image(newdata, xform=img.voxToWorldMat).save(outfile)

    return outfile


def ndvec(infile, ndims):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_ndvec_{}.nii.gz'.format(basename, ndims)
    img      = fslimage.Image(infile)
    data     = img.data

    slc   = []
    shape = []
    for n in range(ndims):
        slc.append(slice(None, None, None))
        shape.append(data.shape[n])
    for n in range(ndims, len(data.shape) - 1):
        slc.append(0)
        shape.append(1)
    slc.append(slice(None, None, None))
    shape.append(3)

    img = fslimage.Image(data[slc].reshape(shape), xform=img.voxToWorldMat)
    img.save(outfile)

    return outfile


def test_overlay_rgbvector():
    extras = {
        'asrgb' : asrgb,
        'ndvec' : ndvec,
    }
    run_cli_tests('test_overlay_rgbvector', cli_tests, extras=extras)
