
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

        realYield(50)

        assert len(overlayList) == 2

        real, imag = overlayList

        # make sure CLI args were applied to both overlays
        assert displayCtx.getOpts(real).cmapResolution == 25
        assert displayCtx.getOpts(imag).cmapResolution == 25
        assert displayCtx.getOpts(real).gamma          == 0.5
        assert displayCtx.getOpts(imag).gamma          == 0.5

        assert np.all(real[:] == np.real(img[:]))
        assert np.all(imag[:] == np.imag(img[:]))
