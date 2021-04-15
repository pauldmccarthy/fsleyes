#!/usr/bin/env python


import os.path as op

from unittest import mock

import wx

import numpy as np

import fsl.data.image as fslimage
from fsl.utils.tempdir import tempdir
import fsleyes.plugins.tools.sampleline as sampleline
import fsleyes.plugins.profiles.samplelineprofile as samplelineprofile
import fsleyes.profiles.orthoviewprofile as orthoviewprofile

from fsleyes.tests import (run_with_orthopanel,
                           realYield,
                           mockMouseEvent,
                           MockFileDialog)


datadir = op.join(op.dirname(__file__), '..', 'testdata')

def test_SampleLineDataSeries():
    run_with_orthopanel(_test_SampleLineDataSeries)
def _test_SampleLineDataSeries(panel, overlayList, displayCtx):

    img = fslimage.Image(op.join(datadir, '3d'))
    overlayList.append(img)
    realYield()

    # centre of first voxel to centre of last voxel
    start = [0, 0, 0]
    end   = [0, 0, img.shape[2] - 1]
    ds    = sampleline.SampleLineDataSeries(
        img, overlayList, displayCtx, None, slice(None), start, end)

    ds.resolution = img.shape[2]

    # testdata/3d has 2mm isotropic pixdms, so
    # x data should be scaled accordingly
    expx = np.arange(0, 2 * img.shape[2], 2)
    expy = img[0, 0, :]
    x, y = ds.getData()
    assert np.all(np.isclose(x, expx))
    assert np.all(np.isclose(y, expy))

    ds.normalise = 'x'
    expx = expx / expx.max()
    x, y = ds.getData()
    assert np.all(np.isclose(x, expx))
    assert np.all(np.isclose(y, expy))

    ds.normalise = 'y'
    expx = np.arange(0, 2 * img.shape[2], 2)
    expy = (expy - expy.min()) / (expy.max() - expy.min())
    x, y = ds.getData()
    assert np.all(np.isclose(x, expx))
    assert np.all(np.isclose(y, expy))

    ds.normalise = 'xy'
    expx = expx / expx.max()
    x, y = ds.getData()
    assert np.all(np.isclose(x, expx))
    assert np.all(np.isclose(y, expy))


def test_SampleLineAction():
    run_with_orthopanel(_test_SampleLineAction)
def _test_SampleLineAction(panel, overlayList, displayCtx):

    act = sampleline.SampleLineAction(overlayList, displayCtx, panel)

    act()
    realYield()
    assert panel.isPanelOpen(sampleline.SampleLinePanel)
    assert isinstance(panel.currentProfile,
                      samplelineprofile.SampleLineProfile)

    act()
    realYield()
    assert not panel.isPanelOpen(sampleline.SampleLinePanel)
    assert type(panel.currentProfile) == orthoviewprofile.OrthoViewProfile


def test_SampleLinePanel():
    run_with_orthopanel(_test_SampleLinePanel)
def _test_SampleLinePanel(panel, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, '3d'))
    overlayList.append(img)
    realYield(5)
    slpanel = panel.togglePanel(sampleline.SampleLinePanel)
    realYield(5)

    # testdata/3d is 17, 14, 14, with 2mm voxels
    displayCtx.location = [20, 14, 14]
    profile = panel.currentProfile
    xcanvas = panel.getXCanvas()

    slpanel.resolution = img.shape[2]

    start = [20, 14, 0]
    mid   = [20, 14, 14]
    end   = [20, 14, 26]

    mockMouseEvent(profile, xcanvas, 'LeftMouseDown', start)
    mockMouseEvent(profile, xcanvas, 'LeftMouseDrag', mid)
    mockMouseEvent(profile, xcanvas, 'LeftMouseDrag', end)
    mockMouseEvent(profile, xcanvas, 'LeftMouseUp',   end)
    realYield(5)
    slpanel.addDataSeries()

    ds   = slpanel.canvas.dataSeries[0]
    expx = np.arange(0, 2 * img.shape[2], 2)
    expy = img[10, 7, :]
    x, y = ds.getData()

    assert np.all(np.isclose(x, expx))
    assert np.all(np.isclose(y, expy))

    slpanel.removeDataSeries()

    assert len(slpanel.canvas.dataSeries) == 0



def test_SampleLinePanel_export():
    run_with_orthopanel(_test_SampleLinePanel_export)
def _test_SampleLinePanel_export(panel, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, '3d'))
    overlayList.append(img)
    realYield(5)
    slpanel = panel.togglePanel(sampleline.SampleLinePanel)
    realYield(5)

    start = [0, 0, 0]
    end   = [0, 0, img.shape[2] - 1]
    ds    = sampleline.SampleLineDataSeries(
        img, overlayList, displayCtx, None, slice(None), start, end)
    ds.resolution = img.shape[2]
    slpanel.canvas.dataSeries.append(ds)

    class MockExportDialog:
        coords = 'none'
        modal = wx.ID_OK
        def __init__(self, parent, series):
            assert series == [ds]
        def GetSeries(self):
            return ds
        def ShowModal(self):
            return self.modal
        def GetCoordinates(self):
            return self.coords

    with mock.patch('fsleyes.plugins.tools.sampleline.'
                    'ExportSampledDataDialog', MockExportDialog) as edlg, \
         MockFileDialog() as fdlg, \
         tempdir():

        fdlg.GetPath_retval   = 'sample.txt'
        fdlg.ShowModal_retval = wx.ID_CANCEL

        slpanel.export()
        assert not op.exists('sample.txt')

        fdlg.ShowModal_retval = wx.ID_OK
        edlg.modal = wx.ID_CANCEL
        slpanel.export()
        assert not op.exists('sample.txt')

        edlg.modal = wx.ID_OK
        slpanel.export()
        expdata = img[0, 0, :]
        gotdata = np.loadtxt('sample.txt')
        assert np.all(np.isclose(expdata, gotdata))

        edlg.coords = 'voxel'
        slpanel.export()
        expdata = np.hstack((img[0, 0, :].reshape((-1, 1)), ds.coords.T))
        gotdata = np.loadtxt('sample.txt')
        assert np.all(np.isclose(expdata, gotdata))

        edlg.coords = 'world'
        slpanel.export()
        opts = displayCtx.getOpts(img)
        coords = opts.transformCoords(ds.coords.T, 'voxel', 'world')
        expdata = np.hstack((img[0, 0, :].reshape((-1, 1)), coords))
        gotdata = np.loadtxt('sample.txt')
        assert np.all(np.isclose(expdata, gotdata))
