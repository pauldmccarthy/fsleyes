#!/usr/bin/env python
#
# test_exportdataseries.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op

try:
    from unittest import mock
except ImportError:
    import mock

import wx

import numpy as np

import fsl.utils.tempdir as tempdir
import fsleyes.actions.exportdataseries as eds
import fsleyes.plotting.dataseries      as ds

from fsleyes.tests import run_with_timeseriespanel, realYield


def test_ExportDataSeriesAction():
    run_with_timeseriespanel(_test_ExportDataSeriesAction)

def _test_ExportDataSeriesAction(panel, overlayList, displayCtx):

    class FileDialog(object):
        ShowModal_return = wx.ID_OK
        GetPath_return = None
        def __init__(self, *a, **kwa):
            pass
        def ShowModal(self):
            return FileDialog.ShowModal_return
        def GetPath(self):
            return FileDialog.GetPath_return
    class MessageDialog(object):
        ShowModal_return = wx.ID_OK
        def __init__(self, *a, **kwa):
            pass
        def ShowModal(self):
            return MessageDialog.ShowModal_return

    displayCtx = panel.displayCtx
    act = eds.ExportDataSeriesAction(overlayList, displayCtx, panel)

    ds1 = ds.DataSeries(None, overlayList, displayCtx, panel)
    ds2 = ds.DataSeries(None, overlayList, displayCtx, panel)
    ds1.setData(np.arange(10), np.random.randint(1, 100, 10))
    ds2.setData(np.arange(10), np.random.randint(1, 100, 10))

    panel.canvas.dataSeries.extend((ds1, ds2))
    realYield(500)

    with tempdir.tempdir(), \
         mock.patch('wx.FileDialog', FileDialog), \
         mock.patch('wx.MessageDialog', MessageDialog):

        MessageDialog.ShowModal_return = wx.ID_CANCEL
        act()

        MessageDialog.ShowModal_return = wx.ID_YES
        FileDialog.ShowModal_return = wx.ID_CANCEL
        act()

        MessageDialog.ShowModal_return = wx.ID_NO
        FileDialog.ShowModal_return = wx.ID_OK
        FileDialog.GetPath_return   = 'data.txt'
        act()

        assert op.exists('data.txt')
        os.remove('data.txt')

        MessageDialog.ShowModal_return = wx.ID_YES
        FileDialog.ShowModal_return = wx.ID_OK
        FileDialog.GetPath_return   = 'data.txt'
        act()
        assert op.exists('data.txt')


    act.destroy()
