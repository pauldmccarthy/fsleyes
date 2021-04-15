#!/usr/bin/env python
#
# test_overlay_rgb.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

import pytest

import fsl.data.image as fslimage

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.overlayclitest


cli_tests = """
{{makevol('4d', 3)}} -ot rgb
{{makevol('4d', 4)}} -ot rgb
{{makevol('4d', 3)}} -ot rgb -in linear
{{makevol('4d', 3)}} -ot rgb -in spline

{{makevol('4d', 3)}} -ot rgb -rc 1 1 0
{{makevol('4d', 3)}} -ot rgb -gc 1 1 0
{{makevol('4d', 3)}} -ot rgb -bc 1 1 0

{{makevol('4d', 3)}} -ot rgb -rs
{{makevol('4d', 3)}} -ot rgb -gs
{{makevol('4d', 3)}} -ot rgb -bs
{{makevol('4d', 4)}} -ot rgb -as

{{makevol('4d', 3)}} -ot rgb -rs -sm white
{{makevol('4d', 3)}} -ot rgb -rs -sm black
{{makevol('4d', 3)}} -ot rgb -rs -sm transparent

{{makergb('4d', 3)}} -ot rgb
{{makergb('4d', 4)}} -ot rgb
{{makergb('4d', 3)}} -ot rgb -in linear
{{makergb('4d', 3)}} -ot rgb -in spline

{{makergb('4d', 3)}} -ot rgb -rc 1 1 0
{{makergb('4d', 3)}} -ot rgb -gc 1 1 0
{{makergb('4d', 3)}} -ot rgb -bc 1 1 0

{{makergb('4d', 3)}} -ot rgb -rs
{{makergb('4d', 3)}} -ot rgb -gs
{{makergb('4d', 3)}} -ot rgb -bs
{{makergb('4d', 4)}} -ot rgb -as

{{makergb('4d', 3)}} -ot rgb -rs -sm white
{{makergb('4d', 3)}} -ot rgb -rs -sm black
{{makergb('4d', 3)}} -ot rgb -rs -sm transparent
"""



def makergb(infile, nchannels):

    img    = fslimage.Image(infile)
    indata = img.data[..., :nchannels]

    if nchannels == 3:
        dtype = np.dtype([('R', 'uint8'),
                          ('G', 'uint8'),
                          ('B', 'uint8')])
    else:
        dtype = np.dtype([('R', 'uint8'),
                          ('G', 'uint8'),
                          ('B', 'uint8'),
                          ('A', 'uint8')])

    outdata = np.zeros(indata.shape[:3], dtype=dtype)

    for cn, ci in zip('RGBA', range(nchannels)):
        cd          = indata[..., ci].astype(np.float32)
        lo, hi      = cd.min(), cd.max()
        cd          = (ci + 1) * 255 * (cd - lo) / (hi - lo)
        outdata[cn] = np.round(cd).astype(np.uint8)

    img  = fslimage.Image(outdata, header=img.header)
    name = fslimage.removeExt(op.basename(infile))
    name = '{}_makergb_{}'.format(name, nchannels)

    img.save(name)

    return name



def makevol(infile, nchannels):

    img  = fslimage.Image(infile)
    data = img.data[..., :nchannels]

    newdata = np.zeros(data.shape, dtype=np.uint8)

    for c in range(nchannels):
        d               = data[..., c].astype(np.float32) * (c + 1)
        lo, hi          = d.min(), d.max()
        newdata[..., c] = np.round(255 * (c + 1) * (d - lo) / (hi - lo)).astype(np.uint8)

    img  = fslimage.Image(newdata, header=img.header)
    name = fslimage.removeExt(op.basename(infile))
    name = '{}_makevol_{}'.format(name, nchannels)

    img.save(name)

    return name


def test_overlay_rgb():
    extras = {
        'makergb' : makergb,
        'makevol' : makevol
    }
    run_cli_tests('test_overlay_rgb', cli_tests, extras=extras)
