#!/usr/bin/env python
#
# test_overlay_dtypes.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

import fsl.data.image as fslimage

import numpy as np

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.overlayclitest


cli_tests = """
{{cast('3d', np.float64)}}
{{cast('3d', np.float32)}}
{{cast('3d', np.uint8)}}
{{cast('3d', np.uint16)}}
{{cast('3d', np.int8)}}
{{cast('3d', np.int16)}}
{{cast('3d', np.uint32)}}
{{cast('3d', np.int32)}}
"""


def cast(infile, dtype):

    base    = fslimage.removeExt(infile)
    outfile = '{}_cast_{}'.format(base, dtype.__name__)

    img = fslimage.Image(infile)

    data = img[:].astype(np.float)

    # force range to 0-255 so it looks
    # the same regardless of dtype
    data = 255 * (data - data.min()) / (data.max() - data.min())

    if dtype in (np.int8, np.int16, np.int32):
        data = data - 128

    fslimage.Image(data, header=img.header).save(outfile)
    return outfile


def test_overlay_dtypes():
    extras = {
        'cast' : cast,
        'np'   : np,
    }
    run_cli_tests('test_overlay_dtypes', cli_tests, extras=extras)
