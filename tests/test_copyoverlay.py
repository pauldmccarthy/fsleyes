#!/usr/bin/env python
#
# test_copyoverlay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

try:
    from unittest import mock
except ImportError:
    import mock

import wx

import numpy as np

import fsl.data.image              as fslimage
import fsleyes.actions.copyoverlay as copyoverlay

from . import run_with_orthopanel


def test_copyImage():
    run_with_orthopanel(_test_copyImage)
def _test_copyImage(panel, overlayList, displayCtx):
    img3d = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)), name='img3d')
    img4d = fslimage.Image(np.random.randint(1, 255, (20, 20, 20, 20)), name='img4d')

    overlayList.extend((img3d, img4d))

    # standard copy. Make sure
    # display settings are copied
    displayCtx.getDisplay(img3d).alpha = 75
    displayCtx.getOpts(   img3d).gamma = 0.5
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img3d,
                          name='my cool copy')
    assert len(overlayList) == 3
    # the copy should be inserted directly
    # after the original in the list
    copy = overlayList[1]
    assert np.all(img3d[:] == copy[:])
    assert displayCtx.getDisplay(copy).alpha == 75
    assert displayCtx.getDisplay(copy).name  == 'my cool copy'
    assert displayCtx.getOpts(   copy).gamma == 0.5
    overlayList.remove(copy)

    # without copying display settings
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img3d,
                          copyDisplay=False)
    assert len(overlayList) == 3
    copy = overlayList[1]
    assert np.all(img3d[:] == copy[:])
    assert displayCtx.getDisplay(copy).alpha == 100
    assert displayCtx.getOpts(   copy).gamma == 0
    overlayList.remove(copy)

    # empty mask
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img3d,
                          createMask=True)
    assert len(overlayList) == 3
    copy = overlayList[1]
    assert np.all(copy.shape == img3d.shape)
    assert np.all(copy[:]    == 0)
    overlayList.remove(copy)

    # 4D
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d)
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert np.all(copy[:] == img4d[:])
    overlayList.remove(copy)

    # 4D mask
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          createMask=True)
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert np.all(copy.shape == img4d.shape)
    assert np.all(copy[:] == 0)
    overlayList.remove(copy)

    # 4D current volume
    displayCtx.getOpts(img4d).volume = 6
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          copy4D=False)
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert np.all(copy[:] == img4d[..., 6])
    overlayList.remove(copy)

    # roi
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img3d,
                          roi=((5, 10), (5, 10), (5, 10)))
    assert len(overlayList) == 3
    copy = overlayList[1]
    assert tuple(copy.shape) == (5, 5, 5)
    assert np.all(copy[:] == img3d[5:10, 5:10, 5:10])
    overlayList.remove(copy)

    # roi 4D, unspecified 4th dim bounds
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          roi=((5, 10), (5, 10), (5, 10)))
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert tuple(copy.shape) == (5, 5, 5, 20)
    assert np.all(copy[:] == img4d[5:10, 5:10, 5:10, :])
    overlayList.remove(copy)

    # roi 4D, specified 4th dim bounds
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          roi=((5, 10), (5, 10), (5, 10), (5, 10)))
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert tuple(copy.shape) == (5, 5, 5, 5)
    assert np.all(copy[:] == img4d[5:10, 5:10, 5:10, 5:10])
    overlayList.remove(copy)

    # roi 4D, current volume
    displayCtx.getOpts(img4d).volume = 10
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          copy4D=False,
                          roi=((5, 10), (5, 10), (5, 10)))
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert tuple(copy.shape) == (5, 5, 5)
    assert np.all(copy[:] == img4d[5:10, 5:10, 5:10, 10])
    overlayList.remove(copy)

    # roi, expanding FOV
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img3d,
                          roi=((-5, 25), (-5, 25), (-5, 25)))
    assert len(overlayList) == 3
    copy = overlayList[1]
    assert tuple(copy.shape) == (30, 30, 30)
    assert np.all(copy[5:25, 5:25, 5:25] == img3d[:, :, :])
    overlayList.remove(copy)

    # roi, 4D, expanding FOV
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          roi=((-5, 25), (-5, 25), (-5, 25)))
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert tuple(copy.shape) == (30, 30, 30, 20)
    assert np.all(copy[5:25, 5:25, 5:25, :] == img4d[:, :, :, :])
    overlayList.remove(copy)

    # roi, 4D, current vol
    copyoverlay.copyImage(overlayList,
                          displayCtx,
                          img4d,
                          copy4D=False,
                          roi=((-5, 25), (-5, 25), (-5, 25)))
    assert len(overlayList) == 3
    copy = overlayList[2]
    assert tuple(copy.shape) == (30, 30, 30)
    assert np.all(copy[5:25, 5:25, 5:25] == img4d[:, :, :, 10])
    overlayList.remove(copy)



def test_CopyOverlayAction():
    run_with_orthopanel(_test_CopyOverlayAction)
def _test_CopyOverlayAction(panel, overlayList, displayCtx):

    img3d = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
    img4d = fslimage.Image(np.random.randint(1, 255, (20, 20, 20, 20)))
    overlayList.extend((img3d, img4d))

    class CheckBoxMessageDialog(object):
        ShowModal_return     = wx.ID_YES
        CheckBoxState_return = [False, False, False]
        def __init__(self, *a, **kwa):
            pass
        def ShowModal(self):
            return CheckBoxMessageDialog.ShowModal_return
        def CheckBoxState(self, cb):
            return CheckBoxMessageDialog.CheckBoxState_return[cb]

    with mock.patch('fsleyes_widgets.dialog.CheckBoxMessageDialog',
                    CheckBoxMessageDialog):

        act = copyoverlay.CopyOverlayAction(overlayList,
                                            displayCtx,
                                            panel.frame)

        CheckBoxMessageDialog.ShowModal_return = wx.ID_CANCEL
        act()
        assert len(overlayList) == 2

        displayCtx.selectOverlay(img3d)
        CheckBoxMessageDialog.ShowModal_return = wx.ID_YES
        act()
        assert len(overlayList) == 3
        print(overlayList)
        copy = overlayList[1]
        assert np.all(copy[:] == img3d[:])
        overlayList.remove(copy)

        displayCtx.selectOverlay(img4d)
        act()
        assert len(overlayList) == 3
        copy = overlayList[2]
        assert np.all(copy[:] == img4d[..., 0])
        overlayList.remove(copy)

        CheckBoxMessageDialog.CheckBoxState_return = [False, False, True]
        displayCtx.selectOverlay(img4d)
        act()
        assert len(overlayList) == 3
        copy = overlayList[2]
        assert np.all(copy[:] == img4d[:])
        overlayList.remove(copy)
