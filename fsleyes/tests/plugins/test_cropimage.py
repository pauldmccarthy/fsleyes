#!/usr/bin/env python

import os.path as op

import fsl.data.image as fslimage
import fsleyes.plugins.tools.cropimage as cropimage

from fsleyes.tests import run_with_orthopanel, realYield


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_cropimage():
    run_with_orthopanel(_test_cropimage)
def _test_cropimage(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    overlayList.append(fslimage.Image(op.join(datadir, '3d')))
    realYield()
    act = cropimage.CropImageAction(overlayList, displayCtx, panel)
    act()
    realYield()
