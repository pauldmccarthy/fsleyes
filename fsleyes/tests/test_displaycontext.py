#!/usr/bin/env python
#
# test_displaycontext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os
import os.path as op
import shutil

from   fsl.utils.tempdir      import tempdir
from   fsl.data.image         import Image
import fsleyes.overlay        as     fsloverlay
import fsleyes.displaycontext as     dc

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


def test_overlayOrder():
    run_with_fsleyes(_test_overlayOrder)
def _test_overlayOrder(frame, overlayList, displayCtx):

    img1        = Image(op.join(datadir, '3d.nii.gz'))
    img2        = Image(op.join(datadir, '3d.nii.gz'))
    img3        = Image(op.join(datadir, '3d.nii.gz'))

    ovlist = fsloverlay.OverlayList()
    dctx   = dc.DisplayContext(ovlist)

    ovlist.extend((img1, img2))
    assert dctx.overlayOrder         == [0, 1]
    assert dctx.getOrderedOverlays() == [img1, img2]

    dctx.overlayOrder                =  [1, 0]
    assert dctx.getOrderedOverlays() == [img2, img1]

    ovlist.append(img3)
    assert dctx.overlayOrder         == [1, 0, 2]
    assert dctx.getOrderedOverlays() == [img2, img1, img3]

    dctx.overlayOrder                =  [2, 1, 0]
    assert dctx.getOrderedOverlays() == [img3, img2, img1]

    ovlist.remove(img1)
    assert dctx.overlayOrder         == [1, 0]
    assert dctx.getOrderedOverlays() == [img3, img2]
