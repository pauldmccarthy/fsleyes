#!/usr/bin/env python

import os.path as op

import fsl.data.image as fslimage
import fsleyes.plugins.tools.edittransform as edittransform

from fsleyes.tests import run_with_orthopanel, realYield


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_edittransform():
    run_with_orthopanel(_test_edittransform)
def _test_edittransform(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    overlayList.append(fslimage.Image(op.join(datadir, '3d')))
    realYield()
    act = edittransform.EditTransformAction(overlayList, displayCtx, panel)
    act()
    realYield()
