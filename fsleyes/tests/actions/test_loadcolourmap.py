#!/usr/bin/env python


import contextlib
import os
import os.path as op
import textwrap as tw

try:
    from unittest import mock
except ImportError:
    import mock

import numpy as np

import wx

import fsl.data.image    as     fslimage
from   fsl.utils.tempdir import tempdir

import fsleyes.actions.loadcolourmap as loadcm
import fsleyes.colourmaps            as fslcm

from fsleyes.tests import (run_with_orthopanel,
                           realYield,
                           clearCmaps,
                           MockFileDialog,
                           MockTextEntryDialog,
                           MockMessageDialog,
                           mockFSLDIR,
                           mockSettingsDir)


def test_LoadColourMapAction():
    run_with_orthopanel(_test_LoadColourMapAction)

def _test_LoadColourMapAction(panel, overlayList, displayCtx):

    with tempdir(),                     \
         mockSettingsDir(),             \
         MockFileDialog()      as fdlg, \
         MockTextEntryDialog() as tdlg, \
         MockMessageDialog()   as mdlg:

        cmapfile = 'mycmap.cmap'

        with open(cmapfile, 'wt') as f:
            f.write(tw.dedent("""
            0 0 0
            0 0 1
            1 0 0
            1 0 1
            """.strip()))

        act = loadcm.LoadColourMapAction(overlayList, displayCtx)
        fdlg.ShowModal_retval = wx.ID_CANCEL
        act()
        assert not fslcm.isColourMapRegistered('mycmap')

        fdlg.ShowModal_retval = wx.ID_OK
        fdlg.GetPath_retval   = cmapfile
        tdlg.ShowModal_retval = wx.ID_CANCEL
        act()
        assert not fslcm.isColourMapRegistered('mycmap')

        with clearCmaps():
            fslcm.init()
            fdlg.ShowModal_retval = wx.ID_OK
            fdlg.GetPath_retval   = cmapfile
            tdlg.ShowModal_retval = wx.ID_OK
            tdlg.GetValue_retval  = 'mycmap'
            mdlg.ShowModal_retval = wx.ID_NO
            act()
            assert     fslcm.isColourMapRegistered('mycmap')
            assert not fslcm.isColourMapInstalled( 'mycmap')

        with clearCmaps():
            fslcm.init()
            fdlg.ShowModal_retval = wx.ID_OK
            fdlg.GetPath_retval   = cmapfile
            tdlg.ShowModal_retval = wx.ID_OK
            tdlg.GetValue_retval  = 'mycmap'
            mdlg.ShowModal_retval = wx.ID_YES
            act()
            print()
            for c in fslcm.getColourMaps():
                print(c)
            print()

            assert fslcm.isColourMapRegistered('mycmap')
            assert fslcm.isColourMapInstalled( 'mycmap')
