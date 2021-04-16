#!/usr/bin/env python


import os.path as op

import pytest

import numpy as np

import fsl.data.image      as fslimage

from fsleyes.tests import run_cli_tests, haveGL21


pytestmark = pytest.mark.overlayclitest


# 3d.nii.gz min - max: 1993 - 7641
# xslice.min(), xslice.max()  (2203, 7229)
# yslice.min(), yslice.max()  (2087, 7452)
# zslice.min(), zslice.max()  (2034, 7282)
# -> 2034, 7452
cli_tests = """
3d.nii.gz -ot mask
3d.nii.gz -ot mask -mc 1 0 0
3d.nii.gz -ot mask -mc 1 0 0
3d.nii.gz -ot mask -mc 1 0 0 -a 70
3d.nii.gz -ot mask -t  0    10000
3d.nii.gz -ot mask -t  2033 10000
3d.nii.gz -ot mask -t  2034 10000
3d.nii.gz -ot mask -t  2035 10000
3d.nii.gz -ot mask -t  2100 10000
3d.nii.gz -ot mask -t  0    7453
3d.nii.gz -ot mask -t  0    7452
3d.nii.gz -ot mask -t  0    7451
3d.nii.gz -ot mask -t  0    7450
3d.nii.gz -ot mask -t  0    7400
3d.nii.gz -ot mask -t  3200 6100

{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   10
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   0
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   0.1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   0.5
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   0.9
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t -1   1.1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  0   0.1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  0   0.9
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  0   1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  0   1.1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  0.9 1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  0.9 1.1
{{binarise('3d.nii.gz', 3200, 6100)}} -ot mask -t  1   1.1

4d.nii.gz -ot mask -t 6800 11000 -v 0
4d.nii.gz -ot mask -t 6800 11000 -v 1
4d.nii.gz -ot mask -t 6800 11000 -v 2
4d.nii.gz -ot mask -t 6800 11000 -v 3
4d.nii.gz -ot mask -t 6800 11000 -v 4

# scaling by 255 because linux has a problem with
# interpolating between 0 and 1 in uint8 textures.
# Understandable, really.
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask -o
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask -o -ow 5
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask          -in linear
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask -o       -in linear
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask -o -ow 5 -in linear
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask          -in spline
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask -o       -in spline
{{binarise('3d.nii.gz', 3200, 6100, 255)}} -ot mask -o -ow 5 -in spline
"""



def binarise(infile, low, high, scale=1):

    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_binarised_{}_{}_{}.nii.gz'.format(
        basename, low, high, scale)
    img      = fslimage.Image(infile)
    data     = img[:]
    binned   = ((data > low) & (data < high)).astype(np.uint8) * scale

    fslimage.Image(binned, header=img.header).save(outfile)

    return outfile

@pytest.mark.skipif('not haveGL21()')
def test_overlay_mask():
    extras = {
        'binarise' : binarise,
    }
    run_cli_tests('test_overlay_mask', cli_tests, extras=extras)
