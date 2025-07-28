#!/usr/bin/env python
#

import os.path as op

import wx

import fsleyes.frame as fslframe
from fsleyes.views.viewpanel import ViewPanel
from fsleyes.views.orthopanel import OrthoPanel
from fsleyes.views.timeseriespanel import TimeSeriesPanel
from fsleyes.views.shellpanel import ShellPanel

from fsleyes.tests import run_with_orthopanel, realYield


def test_droptarget():
    run_with_orthopanel(_test_droptarget)


def _test_droptarget(panel, overlayList, displayCtx):

    datadir = op.join(op.dirname(__file__), 'testdata')
    filename = op.join(datadir, '3d.nii.gz')
    dt = fslframe.OverlayDropTarget(overlayList, displayCtx)
    dt.OnDropFiles(0, 0, [filename])
    realYield(50)
    assert overlayList[0].dataSource == filename


def test_viewPanelLocationAndSize():

    class CustomPanel(ViewPanel):

        @staticmethod
        def defaultLocation():
            return wx.LEFT, 0.75

    tests = [
        (OrthoPanel,      100, 100, None,   None, (wx.RIGHT,  50, 100)),
        (TimeSeriesPanel, 100, 100, None,   None, (wx.BOTTOM, 100, 33)),
        (ShellPanel,      100, 100, None,   None, (wx.BOTTOM, 100, 20)),
        (CustomPanel,     100, 100, None,   None, (wx.LEFT,   75, 100)),
        (OrthoPanel,      100, 100, wx.TOP, None, (wx.TOP,    100, 50)),
        (TimeSeriesPanel, 100, 100, wx.TOP, None, (wx.TOP,    100, 33)),
        (ShellPanel,      100, 100, wx.TOP, None, (wx.TOP,    100, 20)),
        (CustomPanel,     100, 100, wx.TOP, None, (wx.TOP,    100, 75)),
        (OrthoPanel,      100, 100, None,   0.27, (wx.RIGHT,  27, 100)),
        (TimeSeriesPanel, 100, 100, None,   0.27, (wx.BOTTOM, 100, 27)),
        (ShellPanel,      100, 100, None,   0.27, (wx.BOTTOM, 100, 27)),
        (CustomPanel,     100, 100, None,   0.27, (wx.LEFT,   27, 100)),
        (OrthoPanel,      100, 100, wx.TOP, 0.27, (wx.TOP,    100, 27)),
        (TimeSeriesPanel, 100, 100, wx.TOP, 0.27, (wx.TOP,    100, 27)),
        (ShellPanel,      100, 100, wx.TOP, 0.27, (wx.TOP,    100, 27)),
        (CustomPanel,     100, 100, wx.TOP, 0.27, (wx.TOP,    100, 27)),
    ]

    for panelCls, width, height, location, size, expect in tests:
        got = fslframe.FSLeyesFrame.viewPanelLocationAndSize(
            panelCls, width, height, location, size)
        assert got == expect
