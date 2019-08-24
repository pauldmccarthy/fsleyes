
#!/usr/bin/env python
#
# test_complex_image.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import fsl.data.image    as fslimage
import fsl.utils.tempdir as tempdir

import fsleyes.actions.applycommandline as applycommandline

from . import run_with_orthopanel, realYield


def test_complex_image():
    run_with_orthopanel(_test_complex_image)

def _test_complex_image(panel, overlayList, displayCtx):

    with tempdir.tempdir():

        data =      np.random.randint(1, 255, (10, 10, 10)) + \
               1j * np.random.randint(1, 255, (10, 10, 10))
        data = np.array(data, dtype=np.complex64)
        img  = fslimage.Image(data, xform=np.eye(4))
        img.save('complex.nii')

        args = ['complex.nii', '-cmr', '25', '-g', '0.5']

        applycommandline.applyCommandLineArgs(
            overlayList,
            displayCtx,
            args)
        realYield()

        assert len(overlayList) == 1
        nimg = overlayList[0]
        opts = displayCtx.getOpts(nimg)
        assert np.all(nimg[:] == img[:])

        assert opts.channel == 'real'
        assert opts.cmapResolution == 25
        assert opts.gamma          == 0.5

        overlayList.clear()
        args = ['complex.nii', '-ch', 'imag']
        applycommandline.applyCommandLineArgs(
            overlayList,
            displayCtx,
            args)
        realYield()

        assert len(overlayList) == 1
        nimg = overlayList[0]
        opts = displayCtx.getOpts(nimg)
        assert opts.channel == 'imag'
