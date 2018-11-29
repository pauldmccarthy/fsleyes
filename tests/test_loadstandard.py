#!/usr/bin/env python
#
# test_loadstandard.py -
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

import fsleyes.actions.loadstandard as ls

from . import run_with_orthopanel, realYield, MockFileDialog


def test_LoadStandardAction():
    run_with_orthopanel(_test_LoadStandardAction)

def _test_LoadStandardAction(panel, overlayList, displayCtx):

    frame = panel.frame
    act   = ls.LoadStandardAction(overlayList, displayCtx, frame)

    with MockFileDialog() as dlg:
        dlg.ShowModal_retval = wx.ID_CANCEL
        act()
        assert len(overlayList) == 0

        dlg.ShowModal_retval = wx.ID_OK
        dlg.GetPath_retval   = op.expandvars(
            '$FSLDIR/data/standard/MNI152_T1_2mm')
        dlg.GetPaths_retval  = [op.expandvars(
            '$FSLDIR/data/standard/MNI152_T1_2mm')]

        act()
        realYield(50)
        assert len(overlayList) == 1
