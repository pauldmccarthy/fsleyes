#!/usr/bin/env python
#
# test_displaycontext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os
import os.path as op
import shutil

from fsl.utils.tempdir import tempdir
from fsl.data.image import Image
from fsleyes.tests import run_with_fsleyes, realYield


datadir   = op.join(op.dirname(__file__), 'testdata')
baseimage = op.join(datadir, '3d.nii.gz')

def test_autoNameOverlays():
    run_with_fsleyes(_test_autoNameOverlays)
def _test_autoNameOverlays(frame, overlayList, displayCtx):
    displayCtx.autoNameOverlays = True

    expnames = []

    with tempdir():
        for dirname in 'abcde':
            imagefile = op.join(dirname, 'T1.nii.gz')
            expnames.append(op.join(dirname, 'T1'))
            os.mkdir(dirname)
            shutil.copy(baseimage, imagefile)
            overlayList.append(Image(imagefile))
            realYield()

        names = sorted(displayCtx.getDisplay(o).name for o in overlayList)
        assert names == expnames
