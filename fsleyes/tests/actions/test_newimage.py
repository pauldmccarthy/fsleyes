#!/usr/bin/env python
#
# test_newimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock

import wx
import numpy as np

import fsl.data.constants   as constants
import fsl.transform.affine as fslaffine

import fsleyes.actions.newimage as newimage
from fsleyes.tests import run_with_fsleyes, run_with_orthopanel, realYield


class MockNewImageDialog(object):
    initOverride = False

    def __init__(self, parent, shape, pixdim, affine, dtype):
        if MockNewImageDialog.initOverride:
            MockNewImageDialog.shapeRet  = shape
            MockNewImageDialog.pixdimRet = pixdim
            MockNewImageDialog.affineRet = affine
            MockNewImageDialog.dtypeRet  = dtype

    def ShowModal(self):
        return getattr(MockNewImageDialog, 'ShowModalRet', wx.ID_OK)

    @property
    def link(self):
        return getattr(MockNewImageDialog, 'linkRet', True)

    @property
    def shape(self):
        return getattr(MockNewImageDialog, 'shapeRet', (100, 100, 100))

    @property
    def pixdim(self):
        return getattr(MockNewImageDialog, 'pixdimRet', (1, 1, 1))

    @property
    def affine(self):
        return getattr(MockNewImageDialog, 'affineRet', np.eye(4))

    @property
    def dtype(self):
        return getattr(MockNewImageDialog, 'dtypeRet', np.float32)


def test_newImage():
    shape  = (10, 20, 30)
    pixdim = (1.3, -5.4, 3.2)
    dtype  = np.uint8
    affine = fslaffine.compose((2, 3, 4), (-20, 15, 25), (1.5, 1.2, -2.1))

    img    = newimage.newImage(shape, pixdim, dtype, affine)

    assert tuple( img.shape)        == shape
    assert tuple( img.pixdim)       == tuple(np.abs(pixdim))
    assert        img.dtype         == dtype
    assert np.all(img.voxToWorldMat == affine)
    assert        img.xyzUnits      == constants.NIFTI_UNITS_MM
    assert        img.timeUnits     == constants.NIFTI_UNITS_SEC
    assert        img.name          == 'new'

    img = newimage.newImage(shape, pixdim, dtype, affine,
                            xyzUnits=constants.NIFTI_UNITS_METER,
                            timeUnits=constants.NIFTI_UNITS_MSEC,
                            name='whaa')

    assert tuple( img.shape)        == shape
    assert tuple( img.pixdim)       == tuple(np.abs(pixdim))
    assert        img.dtype         == dtype
    assert np.all(img.voxToWorldMat == affine)
    assert        img.xyzUnits      == constants.NIFTI_UNITS_METER
    assert        img.timeUnits     == constants.NIFTI_UNITS_MSEC
    assert        img.name          == 'whaa'


def test_NewImageAction():
    run_with_orthopanel(_test_NewImageAction)

def _test_NewImageAction(panel, overlayList, displayCtx):
    act = panel.frame.menuActions[newimage.NewImageAction]

    def check(ovl, shape, pixdim, dtype, affine):
        assert tuple( ovl.shape)        == tuple(shape)
        assert tuple( ovl.pixdim)       == tuple(pixdim)
        assert        ovl.dtype         == dtype
        assert np.all(ovl.voxToWorldMat == affine)

    tests = [
        ((100, 100, 100), (1,   1,   1),   np.float32, np.eye(4)),
        (( 50,  50,  50), (2,   2,   2),   np.uint8,   np.diag([2, 2, 2, 1])),
        (( 20,  30,  40), (1.5, 1.2, 1.3), np.int32,   fslaffine.scaleOffsetXform([2, 3, 4], [-4, -3, -2])),
        ((100, 100, 100), (1,   1,   1),   np.float64, fslaffine.compose((2, 3, 1), (1, 2, 3), (1, 1.5, 2))),
    ]

    with mock.patch('fsleyes.actions.newimage.NewImageDialog', MockNewImageDialog):
        MockNewImageDialog.ShowModalRet = wx.ID_CANCEL
        MockNewImageDialog.initOverride = False
        act()
        realYield()
        assert len(overlayList) == 0

        MockNewImageDialog.ShowModalRet = wx.ID_OK

        for shape, pixdim, dtype, affine in tests:
            MockNewImageDialog.shapeRet  = shape
            MockNewImageDialog.pixdimRet = pixdim
            MockNewImageDialog.dtypeRet  = dtype
            MockNewImageDialog.affineRet = affine
            act()
            realYield()
            assert len(overlayList) == 1
            check(overlayList[0], shape, pixdim, dtype, affine)
            overlayList.clear()
            realYield()


def test_NewImageAction_existing():
    run_with_orthopanel(_test_NewImageAction_existing)

def _test_NewImageAction_existing(panel, overlayList, displayCtx):
    act = panel.frame.menuActions[newimage.NewImageAction]

    img = newimage.newImage((20, 30, 40),
                            (1.5, 1, 2.5),
                            np.int32,
                            fslaffine.compose((-1.5, 1, 2.5),
                                              (-20, 30, 40),
                                              (1.5, 1.2, -1.5)))

    overlayList.append(img)
    realYield()

    with mock.patch('fsleyes.actions.newimage.NewImageDialog', MockNewImageDialog):
        MockNewImageDialog.ShowModalRet = wx.ID_OK
        MockNewImageDialog.initOverride = True
        act()
        realYield()
        assert len(overlayList) == 2

        old, new = overlayList
        assert old.sameSpace(new)
        assert new.dtype == np.int32


def test_NewImageDialog():
    run_with_fsleyes(_test_NewImageDialog)

def _test_NewImageDialog(frame, overlayList, displayCtx):

    dlg = newimage.NewImageDialog(frame, None, None, None, None)

    wx.CallLater(250, dlg.EndModal, wx.ID_CANCEL)
    assert dlg.ShowModal() == wx.ID_CANCEL

    dlg = newimage.NewImageDialog(frame, None, None, None, None)
    wx.CallLater(250, dlg.EndModal, wx.ID_OK)
    assert dlg.ShowModal() == wx.ID_OK
    assert         dlg.shape == (100, 100, 100)
    assert        dlg.pixdim == (1, 1, 1)
    assert np.all(dlg.affine == np.eye(4))
    assert        dlg.dtype  == np.float32

    dlg = newimage.NewImageDialog(frame, None, None, None, None)
    dlg.dtypeWidget     .SetSelection(2)
    dlg.shapeWidgets[ 0].SetValue(20)
    dlg.shapeWidgets[ 1].SetValue(30)
    dlg.shapeWidgets[ 2].SetValue(40)
    dlg.pixdimWidgets[0].SetValue(-2)
    dlg.pixdimWidgets[1].SetValue(2)
    dlg.pixdimWidgets[2].SetValue(2.5)
    dlg._NewImageDialog__onPixdim(None)
    wx.CallLater(250, dlg.EndModal, wx.ID_OK)
    assert dlg.ShowModal() == wx.ID_OK
    assert         dlg.shape == (20, 30, 40)
    assert        dlg.pixdim == (-2, 2, 2.5)
    assert np.all(dlg.affine == np.diag((-2, 2, 2.5, 1)))
    assert        dlg.dtype  == np.int16


    dlg = newimage.NewImageDialog(frame, None, None, None, None)
    dlg.dtypeWidget     .SetSelection(2)
    dlg.shapeWidgets[ 0].SetValue(20)
    dlg.shapeWidgets[ 1].SetValue(30)
    dlg.shapeWidgets[ 2].SetValue(40)
    dlg.pixdimWidgets[0].SetValue(-2)
    dlg.pixdimWidgets[1].SetValue(2)
    dlg.pixdimWidgets[2].SetValue(2.5)
    dlg.linkWidget     .SetValue(False)
    dlg._NewImageDialog__onPixdim(None)
    wx.CallLater(250, dlg.EndModal, wx.ID_OK)
    assert dlg.ShowModal() == wx.ID_OK
    assert         dlg.shape == (20, 30, 40)
    assert        dlg.pixdim == (-2, 2, 2.5)
    assert np.all(dlg.affine == np.eye(4))
    assert        dlg.dtype  == np.int16


    dlg = newimage.NewImageDialog(frame, None, None, None, None)
    dlg.dtypeWidget     .SetSelection(3)
    dlg.shapeWidgets[ 0].SetValue(20)
    dlg.shapeWidgets[ 1].SetValue(30)
    dlg.shapeWidgets[ 2].SetValue(40)
    dlg.affineWidget.SetCellValue((0, 0), '-2.0')
    dlg.affineWidget.SetCellValue((1, 1), '1.5')
    dlg.affineWidget.SetCellValue((2, 2), '1.4')
    dlg._NewImageDialog__onAffine(None)
    wx.CallLater(250, dlg.EndModal, wx.ID_OK)
    assert dlg.ShowModal() == wx.ID_OK
    assert         dlg.shape == (20, 30, 40)
    assert        dlg.pixdim == (-2, 1.5, 1.4)
    assert np.all(dlg.affine == np.diag((-2, 1.5, 1.4, 1)))
    assert        dlg.dtype  == np.int32
