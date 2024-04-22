#!/usr/bin/env python

import os.path as op

import fsl.data.image as fslimage
import fsleyes.plugins.tools.lightboxsample as lbsample

from fsleyes.tests import run_with_lightboxpanel, realYield


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_lightboxsample():
    run_with_lightboxpanel(_test_lightboxsample)
def _test_lightboxsample(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    overlayList.append(fslimage.Image(op.join(datadir, '3d')))
    realYield()
    act = lbsample.LightBoxSampleAction(overlayList, displayCtx, panel)
    act()
    realYield()
