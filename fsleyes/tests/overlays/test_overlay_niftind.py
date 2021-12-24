#!/usr/bin/env python
#
# test_overlay_niftind.py - Test display of >4D images and
#                           associated cli options
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import nibabel as nib
import numpy   as np

import pytest

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.overlayclitest

cli_tests = """
{{ndimage(3, 3, 3, 3)}}       --index 0     -cm random
{{ndimage(3, 3, 3, 3)}}       --index 1     -cm random
{{ndimage(3, 3, 3, 3)}}       --index 2     -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 0,0   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 0,1   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 0,2   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 1,0   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 1,1   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 1,2   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 2,0   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 2,1   -cm random
{{ndimage(3, 3, 3, 3, 3)}}    --index 2,2   -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,0,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,0,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,0,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,1,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,1,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,1,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,2,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,2,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 0,2,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,0,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,0,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,0,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,1,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,1,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,1,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,2,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,2,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 1,2,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,0,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,0,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,0,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,1,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,1,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,1,2 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,2,0 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,2,1 -cm random
{{ndimage(3, 3, 3, 3, 3, 3)}} --index 2,2,2 -cm random
"""


def ndimage(*dims):
    fname = 'ndimage_' + '_'.join(map(str, dims)) + '.nii.gz'
    data  = np.arange(np.prod(dims)).reshape(dims, order='F')
    image = nib.Nifti1Image(data, np.eye(4))
    image.to_filename(fname)
    return fname


def test_overlay_niftind():
    extras = {'ndimage' : ndimage}
    run_cli_tests('test_overlay_niftind', cli_tests, extras=extras)
