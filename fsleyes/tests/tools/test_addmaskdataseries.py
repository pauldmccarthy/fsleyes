#!/usr/bin/env python
#
# test_addmaskdataseries.py -
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

import fsleyes.plugins.tools.addmaskdataseries as amds

from fsleyes.tests import (run_with_timeseriespanel,
                           run_with_fsleyes,
                           simclick,
                           realYield)


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_AddMaskDataSeriesAction():
    run_with_timeseriespanel(_test_AddMaskDataSeriesAction)
def _test_AddMaskDataSeriesAction(panel, overlayList, displayCtx):

    class MaskDialog(object):
        ShowModal_return = wx.ID_OK
        GetChoice_return = 0
        GetCheckBox_return = 0
        def __init__(self, *args, **kwargs):
            pass
        def ShowModal(self):
            return MaskDialog.ShowModal_return
        def GetChoice(self):
            return MaskDialog.GetChoice_return
        def GetCheckBox(self):
            return MaskDialog.GetCheckBox_return

    img  = fslimage.Image(op.join(datadir, '4d'))
    mask = fslimage.Image(
        np.random.randint(0, 10, img.shape[:3]),
        xform=img.voxToWorldMat)
    overlayList.append(img)
    overlayList.append(mask)

    displayCtx = panel.displayCtx

    act = amds.AddMaskDataSeriesAction(overlayList, displayCtx, panel)

    with mock.patch('fsleyes.plugins.tools.addmaskdataseries.MaskDialog',
                    MaskDialog):
        displayCtx.selectOverlay(mask)
        assert not act.enabled
        displayCtx.selectOverlay(img)
        assert act.enabled

        MaskDialog.ShowModal_return = wx.ID_CANCEL
        act()

        MaskDialog.ShowModal_return = wx.ID_OK
        act()

        MaskDialog.ShowModal_return   = wx.ID_OK
        MaskDialog.GetCheckBox_return = True
        act()

    act.destroy()


def test_MaskDialog():
    run_with_fsleyes(_test_MaskDialog)
def _test_MaskDialog(frame, overlayList, displayCtx):

    dlg = amds.MaskDialog(frame, ['a', 'b', 'c'])
    wx.CallLater(500, dlg._MaskDialog__onOkButton, None)
    assert dlg.ShowModal() == wx.ID_OK
    dlg.Destroy()


    dlg = amds.MaskDialog(frame, ['a', 'b', 'c'])
    wx.CallLater(500, dlg._MaskDialog__onCancelButton, None)
    assert dlg.ShowModal() == wx.ID_CANCEL
    dlg.Destroy()

    dlg = amds.MaskDialog(frame, ['a', 'b', 'c'])

    dlg.choice.SetSelection(1)
    dlg.checkbox.SetValue(True)
    wx.CallLater(500, dlg._MaskDialog__onOkButton, None)

    assert dlg.ShowModal() == wx.ID_OK
    assert dlg.GetChoice() == 1
    assert dlg.GetCheckBox()
    dlg.Destroy()
