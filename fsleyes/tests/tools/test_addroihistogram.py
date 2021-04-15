#!/usr/bin/env python
#
# test_addroihistogram.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

try:
    from unittest import mock
except ImportError:
    import mock

import os.path as op

import wx

import numpy as np

import fsl.data.image as fslimage

import fsleyes.plugins.tools.addroihistogram as arh

from fsleyes.tests import run_with_histogrampanel


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_AddROIHistogramAction():
    run_with_histogrampanel(_test_AddROIHistogramAction)
def _test_AddROIHistogramAction(panel, overlayList, displayCtx):

    class MaskDialog(object):
        ShowModal_return = wx.ID_OK
        GetChoice_return = 0
        def __init__(self, *args, **kwargs):
            pass
        def ShowModal(self):
            return MaskDialog.ShowModal_return
        def GetChoice(self):
            return MaskDialog.GetChoice_return

    img  = fslimage.Image(op.join(datadir, '3d'))
    mask = fslimage.Image(
        np.random.randint(0, 10, img.shape[:3]),
        xform=img.voxToWorldMat)
    other = fslimage.Image(
        np.random.randint(0, 10, [5, 26, 46]),
        xform=img.voxToWorldMat)
    overlayList.append(img)
    overlayList.append(mask)
    overlayList.append(other)

    displayCtx = panel.displayCtx

    act = arh.AddROIHistogramAction(overlayList, displayCtx, panel)

    with mock.patch('fsleyes.plugins.tools.addmaskdataseries.MaskDialog',
                    MaskDialog):
        displayCtx.selectOverlay(other)
        assert not act.enabled
        displayCtx.selectOverlay(mask)
        assert act.enabled
        displayCtx.selectOverlay(img)
        assert act.enabled

        MaskDialog.ShowModal_return = wx.ID_CANCEL
        act()

        MaskDialog.ShowModal_return = wx.ID_OK
        act()

    act.destroy()
