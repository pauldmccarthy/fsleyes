#!/usr/bin/env python
#
# test_importdataseries.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

try:
    from unittest import mock
except ImportError:
    import mock

import wx

import numpy as np

import fsl.utils.tempdir as tempdir
import fsleyes.actions.importdataseries as ids

from fsleyes.tests import run_with_timeseriespanel


def test_ImportDataSeriesAction():
    run_with_timeseriespanel(_test_ImportDataSeriesAction)

def _test_ImportDataSeriesAction(panel, overlayList, displayCtx):

    class FileDialog(object):
        ShowModal_return = wx.ID_OK
        GetPath_return = None
        def __init__(self, *a, **kwa):
            pass
        def ShowModal(self):
            return FileDialog.ShowModal_return
        def GetPath(self):
            return FileDialog.GetPath_return
    class MessageBox(object):
        def __init__(self, *a, **kwa):
            pass
    class NumberDialog(object):
        ShowModal_return = wx.ID_OK
        GetValue_return = 0
        def __init__(self, *a, **kwa):
            pass
        def ShowModal(self):
            return NumberDialog.ShowModal_return
        def GetValue(self):
            return NumberDialog.GetValue_return

    displayCtx = panel.displayCtx
    act = ids.ImportDataSeriesAction(overlayList, displayCtx, panel)

    data = np.random.randint(1, 100, (50, 2))

    with tempdir.tempdir(), \
         mock.patch('wx.FileDialog', FileDialog), \
         mock.patch('wx.MessageBox', MessageBox), \
         mock.patch('fsleyes_widgets.numberdialog.NumberDialog', NumberDialog):
        np.savetxt('data.txt', data)

        FileDialog.ShowModal_return = wx.ID_CANCEL
        act()

        FileDialog.ShowModal_return = wx.ID_OK
        FileDialog.GetPath_return   = 'nonexistent.txt'
        act()

        FileDialog.ShowModal_return = wx.ID_OK
        FileDialog.GetPath_return   = 'data.txt'
        NumberDialog.ShowModal_return = wx.ID_OK
        NumberDialog.GetValue_return = 1
        act()

        NumberDialog.ShowModal_return = wx.ID_CANCEL
        NumberDialog.GetValue_return = 1
        act()

    act.destroy()
