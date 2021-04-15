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

import numpy as np

import wx

import fsl.data.image as fslimage
from fsl.utils.tempdir import tempdir
import fsleyes.actions.loadstandard as ls

from fsleyes.tests import (run_with_orthopanel,
                           realYield,
                           MockFileDialog,
                           mockFSLDIR)


def test_LoadStandardAction():
    run_with_orthopanel(_test_LoadStandardAction)

def _test_LoadStandardAction(panel, overlayList, displayCtx):

    with mockFSLDIR(), MockFileDialog() as dlg:

        fsldir = os.environ['FSLDIR']
        stddir = op.join(fsldir, 'data', 'standard')
        fname  = op.join(stddir, 'image.nii.gz')
        img    = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        frame  = panel.frame

        os.makedirs(stddir)
        img.save(fname)

        act = ls.LoadStandardAction(overlayList, displayCtx, frame)
        dlg.ShowModal_retval = wx.ID_CANCEL
        act()
        assert len(overlayList) == 0

        dlg.ShowModal_retval = wx.ID_OK
        dlg.GetPath_retval   =  fname
        dlg.GetPaths_retval  = [fname]

        act()
        realYield(50)
        assert len(overlayList) == 1
