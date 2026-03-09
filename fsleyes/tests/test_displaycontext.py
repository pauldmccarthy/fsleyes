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
        images = []
        for dirname in 'abcde':
            imagefile = op.join(dirname, 'T1.nii.gz')
            expnames.append(op.join(dirname, 'T1'))
            os.mkdir(dirname)
            shutil.copy(baseimage, imagefile)
            images.append(Image(imagefile))

        overlayList.extend(images)
        realYield()

        names = sorted(displayCtx.getDisplay(o).name for o in overlayList)
        assert names == expnames




def test_autoname_do_not_rename_already_named_overlays():
    run_with_fsleyes(_test_autoname_do_not_rename_already_named_overlays)

def _test_autoname_do_not_rename_already_named_overlays(
        ortho, overlayList, displayCtx):

    displayCtx.autoNameOverlays = True

    with tempdir():

        os.makedirs('a/b')
        os.makedirs('a/c', exist_ok=True)

        shutil.copy(f'{datadir}/3d.nii.gz', 'a/b/')
        shutil.copy(f'{datadir}/3d.nii.gz', 'a/c/')

        i1 = Image('a/b/3d')
        i2 = Image('a/c/3d')

        overlayList.extend((i1, i2))
        realYield()

        # normal autoname behaviour
        assert displayCtx.getDisplay(i1).name == 'b/3d'
        assert displayCtx.getDisplay(i2).name == 'c/3d'

        overlayList[:] = []
        realYield()

        # fsl/fsleyes/fsleyes!497
        # don't auto rename  overlays that
        # have explicitly been given a name
        i1 = Image('a/b/3d')
        i2 = Image('a/c/3d')
        overlayList.extend((i1, i2), name={i1 : 'first', i2 : 'second'})
        realYield()
        assert displayCtx.getDisplay(i1).name == 'first'
        assert displayCtx.getDisplay(i2).name == 'second'


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
