#!/usr/bin/env python
#
# test_resample.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

try:
    from unittest import mock
except ImportError:
    import mock

import numpy as np

import wx

import fsl.transform.affine as affine
import fsl.data.image as fslimage

import fsleyes.plugins.tools.resample as resample

from fsleyes.tests import (run_with_fsleyes,
                           run_with_orthopanel,
                           realYield,
                           simtext,
                           simclick)


def test_resample():
    run_with_orthopanel(_test_resample)


def _test_resample(panel, overlayList, displayCtx):


    class ResampleDialog(object):
        ShowModal_return        = None
        GetVoxels_return        = None
        GetPixdims_return       = None
        GetInterpolation_return = None
        GetDataType_return      = None
        GetSmoothing_return     = None
        GetOrigin_return        = 'centre'
        GetReference_return     = None
        GetAllVolumes_return    = None
        def __init__(self, *args, **kwargs):
            pass
        def ShowModal(self):
            return ResampleDialog.ShowModal_return

        def GetVoxels(self):
            return ResampleDialog.GetVoxels_return
        def GetReference(self):
            return ResampleDialog.GetReference_return
        def GetInterpolation(self):
            return ResampleDialog.GetInterpolation_return
        def GetOrigin(self):
            return ResampleDialog.GetOrigin_return
        def GetDataType(self):
            return ResampleDialog.GetDataType_return
        def GetSmoothing(self):
            return ResampleDialog.GetSmoothing_return
        def GetAllVolumes(self):
            return ResampleDialog.GetAllVolumes_return
        def GetPixdims(self):
            return ResampleDialog.GetPixdims_return


    act = resample.ResampleAction(overlayList, displayCtx, panel.frame)

    with mock.patch('fsleyes.plugins.tools.resample.ResampleDialog',
                    ResampleDialog):

        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        overlayList.append(img)
        ResampleDialog.ShowModal_return = wx.ID_CANCEL
        act()
        assert len(overlayList) == 1

        ResampleDialog.ShowModal_return        = wx.ID_OK
        ResampleDialog.GetVoxels_return        = (10, 10, 10)
        ResampleDialog.GetInterpolation_return = 'linear'
        ResampleDialog.GetDataType_return      = np.int32
        ResampleDialog.GetSmoothing_return     = True
        ResampleDialog.GetAllVolumes_return    = True
        ResampleDialog.GetPixdims_return       = (2, 2, 2)
        act()
        assert len(overlayList) == 2
        resampled = overlayList[1]
        assert tuple(resampled.shape)  == (10, 10, 10)
        assert tuple(resampled.pixdim) == (2, 2, 2)
        assert resampled.dtype         == np.int32

        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20, 15)))
        overlayList.clear()
        overlayList.append(img)
        act()
        assert len(overlayList) == 2
        resampled = overlayList[1]
        assert tuple(resampled.shape)  == (10, 10, 10, 15)
        assert tuple(resampled.pixdim) == (2, 2, 2, 1)
        assert resampled.dtype         == np.int32

        overlayList.clear()
        overlayList.append(img)
        ResampleDialog.GetAllVolumes_return = False
        act()
        assert len(overlayList) == 2
        resampled = overlayList[1]
        assert tuple(resampled.shape)  == (10, 10, 10)
        assert tuple(resampled.pixdim) == (2, 2, 2)
        assert resampled.dtype         == np.int32

        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        ref = fslimage.Image(np.random.randint(1, 255, (40, 40, 40)))
        overlayList.clear()
        overlayList[:] = [img, ref]
        ResampleDialog.GetReference_return = ref
        act()
        resampled = overlayList[-1]
        assert resampled.sameSpace(ref)

        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        overlayList[:] = [img]
        ResampleDialog.GetReference_return = None
        ResampleDialog.GetOrigin_return = 'corner'
        act()
        res = overlayList[-1]
        assert np.all(np.isclose(
            np.array(affine.axisBounds(img.shape, img.voxToWorldMat)),
            np.array(affine.axisBounds(res.shape, res.voxToWorldMat))))




def test_ResampleDialog():
    run_with_fsleyes(_test_ResampleDialog)

def _test_ResampleDialog(frame, overlayList, displayCtx):

    sim = wx.UIActionSimulator()

    # click ok
    dlg = resample.ResampleDialog(frame,
                                  'title',
                                  (10, 10, 10),
                                  (1, 1, 1), [])

    wx.CallLater(500, dlg._ResampleDialog__onOk, None)
    assert dlg.ShowModal() == wx.ID_OK
    assert dlg.GetReference() is None

    # click cancel
    dlg = resample.ResampleDialog(frame,
                                  'title',
                                  (10, 10, 10),
                                  (1, 1, 1), [])
    wx.CallLater(500, dlg._ResampleDialog__onCancel, None)
    assert dlg.ShowModal() == wx.ID_CANCEL

    # set voxel dims
    dlg = resample.ResampleDialog(frame,
                                  'title',
                                  (10, 10, 10),
                                  (1, 1, 1), [])
    wx.CallLater(300,  simtext,  sim, dlg.voxXCtrl.textCtrl, '20')
    wx.CallLater(400,  simtext,  sim, dlg.voxYCtrl.textCtrl, '40')
    wx.CallLater(500,  simtext,  sim, dlg.voxZCtrl.textCtrl, '80')
    wx.CallLater(1000, dlg._ResampleDialog__onOk, None)
    dlg.ShowModal()
    assert dlg.GetVoxels()  == (20,  40,   80)
    assert dlg.GetPixdims() == (0.5, 0.25, 0.125)
    dlg.Destroy()


    # set pixdims
    dlg = resample.ResampleDialog(frame,
                                  'title',
                                  (10, 10, 10),
                                  (1, 1, 1), [])

    wx.CallLater(300,  simtext,  sim, dlg.pixXCtrl.textCtrl, '0.5')
    wx.CallLater(400,  simtext,  sim, dlg.pixYCtrl.textCtrl, '0.25')
    wx.CallLater(500,  simtext,  sim, dlg.pixZCtrl.textCtrl, '0.125')
    wx.CallLater(1000, dlg._ResampleDialog__onOk, None)
    dlg.ShowModal()
    assert dlg.GetVoxels()  == (20,  40,   80)
    assert dlg.GetPixdims() == (0.5, 0.25, 0.125)
    dlg.Destroy()

    # reset
    dlg = resample.ResampleDialog(frame,
                                  'title',
                                  (10, 10, 10),
                                  (1, 1, 1), [])
    wx.CallLater(300,  simtext,  sim, dlg.pixXCtrl.textCtrl, '0.5')
    wx.CallLater(400,  simtext,  sim, dlg.pixYCtrl.textCtrl, '0.25')
    wx.CallLater(500,  simtext,  sim, dlg.pixZCtrl.textCtrl, '0.125')
    wx.CallLater(1000, dlg._ResampleDialog__onReset, None)
    wx.CallLater(1500, dlg._ResampleDialog__onOk, None)
    dlg.ShowModal()
    assert dlg.GetVoxels()  == (10, 10, 10)
    assert dlg.GetPixdims() == (1, 1, 1)
    dlg.Destroy()

    # set options
    i1 = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)),
                        name='i1')
    i2 = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)),
                        name='i2')
    dlg = resample.ResampleDialog(frame,
                                  'title',
                                  (10, 10, 10, 10),
                                  (1, 1, 1), [i1, i2])

    dlg.interpCtrl.SetSelection(1)
    dlg.dtypeCtrl .SetSelection(1)
    dlg.originCtrl.SetSelection(1)
    dlg.refCtrl   .SetSelection(2)

    origSmooth  = dlg.GetSmoothing()
    origAllVols = dlg.GetAllVolumes()

    dlg.smoothCtrl.SetValue(not origSmooth)
    dlg.allVolumesCtrl.SetValue(not origAllVols)
    wx.CallLater(500, dlg._ResampleDialog__onOk, None)
    dlg.ShowModal()
    assert dlg.GetSmoothing()     == (not origSmooth)
    assert dlg.GetAllVolumes()    == (not origAllVols)
    assert dlg.GetInterpolation() == 'nearest'
    assert dlg.GetOrigin()        == 'corner'
    assert dlg.GetDataType()      == np.uint8
    assert dlg.GetReference()     == i2
    dlg.Destroy()
