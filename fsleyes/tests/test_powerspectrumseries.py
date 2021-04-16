#!/usr/bin/env python
#
# test_powerspectrumseries.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>


import os
import os.path as op

import shutil

from unittest import mock

import numpy as np

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image
from fsl.data.vtk      import VTKMesh

import fsleyes.plotting.powerspectrumseries as psseries

from fsleyes.tests import run_with_powerspectrumpanel, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def test_calcPowerSpectrum():

    # (data, explen, expdtype)
    tests = [
        (np.random.random(99),                               49,  np.floating),
        (np.random.random(100),                              50,  np.floating),
        (np.random.random(99)  + np.random.random(99)  * 1j, 99,  np.complexfloating),
        (np.random.random(100) + np.random.random(100) * 1j, 100, np.complexfloating),
    ]

    for data, explen, expdtype in tests:
        got = psseries.calcPowerSpectrum(data)
        assert got.shape == (explen,)
        assert np.issubdtype(got.dtype, expdtype)


def test_calcFrequencies():

    # (data, explen)
    tests = [
        (np.random.random(99),                               49),
        (np.random.random(100),                              50),
        (np.random.random(99)  + np.random.random(99)  * 1j, 99),
        (np.random.random(100) + np.random.random(100) * 1j, 100),
    ]

    for data, explen in tests:
        got = psseries.calcFrequencies(len(data), 1, data.dtype)
        assert got.shape == (explen,)


def test_magnitude():
    assert np.isclose(psseries.magnitude(3 + 4j), 5.0)


def test_phase():
    assert np.isclose(psseries.phase(4 + 4j), np.pi / 4)

def test_normalise():
    data = np.array([1, 2, 3, 4, 5])
    assert np.all(psseries.normalise(data) == np.linspace(-1, 1, 5))

def test_phaseCorrection():
    data      = np.random.random(100) + np.random.random(100) * 1j
    spectrum  = psseries.calcPowerSpectrum(data)
    freqs     = psseries.calcFrequencies(len(data), 1, data.dtype)
    corrected = psseries.phaseCorrection(spectrum, freqs, 1, 2)

    # TODO write a real test
    assert corrected.shape == spectrum.shape


def test_VoxelPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_VoxelPowerSpectrumSeries)

def _test_VoxelPowerSpectrumSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    img = Image(op.join(datadir, '4d'))
    overlayList.append(img)
    realYield()
    opts    = displayCtx.getOpts(img)
    ps      = panel.getDataSeries(img)
    x, y, z = img.shape[0] // 2, img.shape[1] // 2, img.shape[2] // 2
    loc     = opts.transformCoords((x, y, z), 'voxel', 'display')
    displayCtx.location = loc
    realYield()

    expx = psseries.calcFrequencies(img.shape[3], img.pixdim[3], img.dtype)
    expy = psseries.calcPowerSpectrum(img[x, y, z, :])

    xdata, ydata = ps.getData()
    assert ps.sampleTime == img.pixdim[3]
    assert np.all(xdata  == expx)
    assert np.all(ydata  == expy)

    ps.varNorm = True

    expy = psseries.normalise(expy)
    ydata = ps.getData()[1]
    assert np.all(ydata  == expy)

    ps.varNorm = False

    x = x - 1
    y = y + 1
    z = z - 1

    loc = opts.transformCoords((x, y, z), 'voxel', 'display')
    displayCtx.location = loc
    realYield()
    xdata, ydata = ps.getData()
    expx = psseries.calcFrequencies(img.shape[3], img.pixdim[3], img.dtype)
    expy = psseries.calcPowerSpectrum(img[x, y, z, :])

    assert np.all(xdata == expx)
    assert np.all(ydata == expy)


def test_ComplexPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_ComplexPowerSpectrumSeries)

def _test_ComplexPowerSpectrumSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    data       = np.random.randint(1, 255, (10, 10, 10, 20)) + \
            1j * np.random.randint(1, 255, (10, 10, 10, 20))
    data = np.array(data, dtype=np.complex64)
    img  = Image(data, xform=np.eye(4))
    overlayList.append(img)
    realYield(100)
    opts = displayCtx.getOpts(img)
    ps   = panel.getDataSeries(img)
    displayCtx.location = opts.transformCoords((7, 8, 9), 'voxel', 'display')

    expx = psseries.calcFrequencies(  img.shape[3], 1, img.dtype)
    expy = psseries.calcPowerSpectrum(img[7, 8, 9, :])

    xdata, ydata = ps.getData()
    assert np.all(xdata == expx)
    assert np.all(ydata == expy.real)

    ps.plotReal = False
    xdata, ydata = ps.getData()
    assert xdata is None
    assert ydata is None

    ps.plotImaginary = True
    ps.plotMagnitude = True
    ps.plotPhase     = True
    ips, mps, pps = ps.extraSeries()

    assert np.all(np.isclose(expy.imag,                ips.getData()[1]))
    assert np.all(np.isclose(psseries.magnitude(expy), mps.getData()[1]))
    assert np.all(np.isclose(psseries.phase(    expy), pps.getData()[1]))

    ps.plotReal                  = True
    ps.zeroOrderPhaseCorrection  = 1
    ps.firstOrderPhaseCorrection = 2

    exp = psseries.phaseCorrection(expy, expx, 1, 2)
    assert np.all(np.isclose(exp.real,                ps .getData()[1]))
    assert np.all(np.isclose(exp.imag,                ips.getData()[1]))
    assert np.all(np.isclose(psseries.magnitude(exp), mps.getData()[1]))
    assert np.all(np.isclose(psseries.phase(    exp), pps.getData()[1]))


def test_MelodicPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_MelodicPowerSpectrumSeries)

def _test_MelodicPowerSpectrumSeries(panel, overlayList, displayCtx):

    class MockMelodicImage(Image):
        def getComponentPowerSpectrum(self, comp):
            x, y, z = self.shape[0] // 2, self.shape[1] // 2, self.shape[2] // 2
            return self[x, y, z, :] * comp

    with tempdir(), mock.patch('fsl.data.melodicimage.MelodicImage',
                               MockMelodicImage):
        displayCtx = panel.displayCtx
        img = MockMelodicImage(op.join(datadir, '4d'))
        overlayList.append(img)
        realYield()
        opts    = displayCtx.getOpts(img)
        ps      = panel.getDataSeries(img)
        x, y, z = img.shape[0] // 2, img.shape[1] // 2, img.shape[2] // 2
        loc     = opts.transformCoords((x, y, z), 'voxel', 'display')
        displayCtx.location = loc
        realYield()
        expbase = img[x, y, z, :]
        assert np.all(ps.getData()[1] == expbase * 0)
        opts.volume = 1
        realYield()
        assert np.all(ps.getData()[1] == expbase * 1)
        opts.volume = 2
        realYield()
        assert np.all(ps.getData()[1] == expbase * 2)


def test_MeshPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_MeshPowerSpectrumSeries)

def _test_MeshPowerSpectrumSeries(panel, overlayList, displayCtx):
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
    exp  = data[10, :]
    expx = psseries.calcFrequencies(len(exp), 1, exp.dtype)
    expy = psseries.calcPowerSpectrum(exp)
    ps = panel.getDataSeries(mesh)

    gotx, goty = ps.getData()
    assert np.all(gotx == expx)
    assert np.all(goty == expy)
