#!/usr/bin/env python

import os.path as op
import warnings

import numpy as np

import wx

from fsl.data.image import Image

from fsleyes.views.orthopanel import OrthoPanel
from fsleyes.controls.locationpanel import LocationPanel

from fsleyes.tests import run_with_orthopanel, realYield, simclick


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_LocationPanel_copy_coordinates():
    run_with_orthopanel(_test_LocationPanel_copy_coordinates)

def _test_LocationPanel_copy_coordinates(ortho, overlayList, displayCtx):

    displayCtx = ortho.displayCtx
    sim        = wx.UIActionSimulator()
    cb         = wx.TheClipboard

    img = Image(op.join(datadir, '3d'))
    overlayList.append(img)
    realYield()

    if not ortho.isPanelOpen(LocationPanel):
        ortho.togglePanel(LocationPanel)
        realYield()
    location = ortho.getPanel(LocationPanel)

    opts   = displayCtx.getOpts(img)
    expvox = [1, 3, 5]
    expwld = list(opts.transformCoords(expvox, 'voxel', 'world'))
    expdsp = list(opts.transformCoords(expvox, 'voxel', 'display'))
    expcds = expwld + expvox

    displayCtx.location = expdsp
    realYield()

    simclick(sim, location.infoPanel.copyButton)
    realYield()

    if cb.Open():
        dataobj = wx.TextDataObject()
        cb.GetData(dataobj)
        gotcds = np.fromstring(dataobj.GetText(), sep=' ')

        assert np.all(np.isclose(expcds, gotcds))

    else:
        warnings.warn('Could not access clipboard')
