#!/usr/bin/env python


import os
import os.path as op

import shutil

from unittest import mock

import numpy as np

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image
from fsl.data.vtk      import VTKMesh

import fsleyes.plotting as plotting

from fsleyes.tests import run_with_timeseriespanel, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def test_DataSeries():
    ds = plotting.DataSeries('1', '2', '3' ,'4')
    assert ds.overlay     == '1'
    assert ds.overlayList == '2'
    assert ds.displayCtx  == '3'
    assert ds.plotCanvas  == '4'
    assert list(sorted(ds.redrawProperties())) == [
        'alpha',
        'colour',
        'enabled',
        'label',
        'lineStyle',
        'lineWidth']
    assert ds.extraSeries() == []
    ds.setData('a', 'b')
    assert ds.getData() == ('a', 'b')


def test_VoxelTimeSeries():
    run_with_timeseriespanel(_test_VoxelTimeSeries)

def _test_VoxelTimeSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    img = Image(op.join(datadir, '4d'))
    overlayList.append(img)
    realYield()
    opts    = displayCtx.getOpts(img)
    ts      = panel.getDataSeries(img)
    x, y, z = img.shape[0] // 2, img.shape[1] // 2, img.shape[2] // 2
    loc     = opts.transformCoords((x, y, z), 'voxel', 'display')
    displayCtx.location = loc
    realYield()

    xdata, ydata = ts.getData()
    assert np.all(xdata == np.arange(img.shape[3]))
    assert np.all(ydata == img[x, y, z, :])

    loc = opts.transformCoords((x - 1, y + 1, z - 1), 'voxel', 'display')
    displayCtx.location = loc
    realYield()
    xdata, ydata = ts.getData()
    assert np.all(xdata == np.arange(img.shape[3]))
    assert np.all(ydata == img[x - 1, y + 1, z - 1, :])


def test_ComplexTimeSeries():
    run_with_timeseriespanel(_test_ComplexTimeSeries)

def _test_ComplexTimeSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    data       = np.random.randint(1, 255, (10, 10, 10, 20)) + \
            1j * np.random.randint(1, 255, (10, 10, 10, 20))
    data = np.array(data, dtype=np.complex64)
    img  = Image(data, xform=np.eye(4))
    overlayList.append(img)
    realYield(100)
    opts = displayCtx.getOpts(img)
    ts   = panel.getDataSeries(img)
    displayCtx.location = opts.transformCoords((7, 8, 9), 'voxel', 'display')
    exp = img[7, 8, 9, :]

    xdata, ydata = ts.getData()
    assert np.all(xdata == np.arange(img.shape[3]))
    assert np.all(ydata == exp.real)

    ts.plotReal = False
    xdata, ydata = ts.getData()
    assert xdata is None
    assert ydata is None

    ts.plotImaginary = True
    ts.plotMagnitude = True
    ts.plotPhase     = True
    its, mts, pts = ts.extraSeries()
    assert np.all(its.getData()[1] == exp.imag)

    expmag   = np.sqrt(exp.real ** 2 + exp.imag ** 2)
    expphase = np.arctan2(exp.imag, exp.real)

    assert np.all(np.isclose(expmag,   mts.getData()[1]))
    assert np.all(np.isclose(expphase, pts.getData()[1]))



def test_FEATTimeSeries():
    run_with_timeseriespanel(_test_FEATTimeSeries)

def _test_FEATTimeSeries(panel, overlayList, displayCtx):

    class MockFEATImage(Image):
        def numEVs(self):
            return 1
        def numContrasts(self):
            return 1
        def contrastNames(self):
            return ['cope1']
        def contrasts(self):
            return [[1]]
        def hasStats(self):
            return True
        def getDesign(self, xyz):
            x, y, z = xyz
            return np.array(self[x, y, z, :] * 2).reshape((-1, 1))
        def getResiduals(self):
            return np.arange(np.prod(self.shape)).reshape(self.shape)
        def partialFit(self, contrast, xyz):
            x, y, z = xyz
            return self[x, y, z, :] * 5
        def fit(self, contrast, xyz):
            x, y, z = xyz
            return self[x, y, z, :] * 10

    with tempdir(), mock.patch('fsl.data.featimage.FEATImage', MockFEATImage):
        displayCtx = panel.displayCtx
        img = MockFEATImage(op.join(datadir, '4d'))
        overlayList.append(img)
        opts = displayCtx.getOpts(img)
        realYield()
        ts = panel.getDataSeries(img)
        x, y, z = img.shape[0] // 2, img.shape[1] // 2, img.shape[2] // 2
        loc     = opts.transformCoords((x, y, z), 'voxel', 'display')
        displayCtx.location = loc
        realYield()
        assert np.all(ts.getData()[1] == img[x,y, z, :])
        ts.plotData = False
        assert ts.getData() == (None, None)
        fmf = ts.extraSeries()[0]
        assert np.all(fmf.getData()[1] == img.fit(0, (x, y, z)))
        ts.plotFullModelFit = False
        ts.plotResiduals = True
        rf = ts.extraSeries()[0]
        assert np.all(rf.getData()[1] == img.getResiduals()[x, y, z, :])
        ts.plotResiduals = False
        ts.plotEVs[0] = True
        ef = ts.extraSeries()[0]
        assert np.all(ef.getData()[1] == img.getDesign((x, y, z))[:, 0])
        ts.plotEVs[0] = False
        ts.plotPEFits[0] = True
        pf = ts.extraSeries()[0]
        assert np.all(pf.getData()[1] == img.fit(0, (x, y, z)))
        ts.plotPEFits[0] = False
        ts.plotCOPEFits[0] = True
        pf = ts.extraSeries()[0]
        assert np.all(pf.getData()[1] == img.fit(0, (x, y, z)))
        ts.plotCOPEFits[0] = False
        ts.plotPartial = 'PE1'
        pf = ts.extraSeries()[0]
        assert np.all(pf.getData()[1] == img.partialFit(0, (x, y, z)))


def test_MelodicTimeSeries():
    run_with_timeseriespanel(_test_MelodicTimeSeries)

def _test_MelodicTimeSeries(panel, overlayList, displayCtx):
    class MockMelodicImage(Image):
        def getComponentTimeSeries(self, comp):
            x, y, z = self.shape[0] // 2, self.shape[1] // 2, self.shape[2] // 2
            return self[x, y, z, :] * comp

    with tempdir(), mock.patch('fsl.data.melodicimage.MelodicImage',
                               MockMelodicImage):
        displayCtx = panel.displayCtx
        img = MockMelodicImage(op.join(datadir, '4d'))
        overlayList.append(img)
        opts = displayCtx.getOpts(img)
        realYield()
        ts = panel.getDataSeries(img)
        x, y, z = img.shape[0] // 2, img.shape[1] // 2, img.shape[2] // 2
        loc     = opts.transformCoords((x, y, z), 'voxel', 'display')
        displayCtx.location = loc
        realYield()
        expbase = img[x, y, z, :]
        assert np.all(ts.getData()[1] == expbase * 0)
        opts.volume = 1
        realYield()
        assert np.all(ts.getData()[1] == expbase * 1)
        opts.volume = 2
        realYield()
        assert np.all(ts.getData()[1] == expbase * 2)


def test_MeshTimeSeries():
    run_with_timeseriespanel(_test_MeshTimeSeries)

def _test_MeshTimeSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx

    mesh = VTKMesh(op.join(datadir, 'mesh_l_thal.vtk'))
    mesh.loadVertexData(op.join(datadir, 'mesh_l_thal_data4d.txt'))
    data = np.loadtxt(op.join(datadir, 'mesh_l_thal_data4d.txt'))
    overlayList.append(mesh)
    realYield()
    opts = displayCtx.getOpts(mesh)
    opts.vertexData = mesh.vertexDataSets()[0]

    displayCtx.location = opts.transformCoords(
        mesh.vertices[10, :], 'mesh', 'display')
    realYield()
    exp = data[10, :]
    ts = panel.getDataSeries(mesh)
    assert np.all(ts.getData()[1] == exp)
