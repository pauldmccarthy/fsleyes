#!/usr/bin/env python
#
# test_histogramseries.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op

import shutil

from unittest import mock

import numpy as np

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image
from fsl.data.vtk      import VTKMesh

import fsleyes.plotting.histogramseries as hseries

from fsleyes.tests import run_with_histogrampanel, realYield

datadir = op.join(op.dirname(__file__), 'testdata')


def test_histogram():

    def check(bins, counts):
        for i, blo in enumerate(bins[:-1]):
            count = counts[i]
            bhi   = bins[  i + 1]
            if i + 1 == len(hx) - 1:
                exp = len([v for v in data if v >= blo and v <= bhi])
            else:
                exp = len([v for v in data if v >= blo and v <  bhi])
            assert count == exp

    data = np.random.randint(1, 100, 1000)
    dmin = data.min()
    dmax = data.max()
    hx, hy, nvals = hseries.histogram(data, 10, (dmin, dmax), (dmin, dmax))
    assert np.all(hx == np.linspace(dmin, dmax, 11))
    assert len(hy) == 10
    assert nvals   == 1000
    check(hx, hy)

    hx, hy, nvals = hseries.histogram(data, 10, (dmin, dmax), (dmin, dmax), count=False)
    check(hx, hy * nvals)

    hx, hy, nvals = hseries.histogram(data, 8, (10, 90), (dmin, dmax))
    assert np.all(hx == np.linspace(10, 90, 9))
    assert len(hy)   == 8
    check(hx, hy)

    hx, hy, nvals = hseries.histogram(data, 8, (10, 90), (dmin, dmax), includeOutliers=True)
    expbins = list(np.linspace(10, 90, 9))
    expbins[0]  = dmin
    expbins[-1] = dmax
    assert np.all(hx == expbins)
    assert len(hy)   == 8
    check(hx, hy)


def test_autoBin():

    tests = [
        (np.random.random(100),            (0, 1)),
        (np.random.random(100),            (0, 0)),
        (np.random.random(1000),           (0, 1)),
        (np.random.randint(1, 100,  100),  (1, 100)),
        (np.random.randint(1, 1000, 1000), (1, 1000)),
    ]

    for data, drange in tests:
        assert hseries.autoBin(data, drange) > 0



def test_HistogramSeries():

    class Overlay(object):
        def name(self):
            return str(id(self))

    hs    = hseries.HistogramSeries(Overlay(), None, None, None)
    data1 = np.random.randint(1,     1000, 1000)
    data2 = np.random.randint(-1000, 1000, 1000)

    hs.setHistogramData(data1, 'data1')

    # HistogramSeries.dataRange upper bound is exclusive
    d1min, d1max  = data1.min(), data1.max()
    drange        = (d1min, d1max + (d1max - d1min) / 10000.0)
    nbins         = hseries.autoBin(data1, drange)

    hx, hy, nvals = hseries.histogram(data1, nbins, drange, drange)

    gotx, goty = hs.getData()

    assert hs.nbins == nbins
    assert hs.numHistogramValues == nvals
    assert np.all(np.isclose(hx, gotx))
    assert np.all(np.isclose(hy, goty))

    hs.autoBin = False
    hs.nbins   = 124
    hx, hy, nvals = hseries.histogram(data1, 124, drange, drange)
    gotx, goty = hs.getData()
    assert np.all(np.isclose(hx, gotx))
    assert np.all(np.isclose(hy, goty))

    drange = (10, 80.1)
    hs.dataRange.x = 10, 80.1
    hx, hy, nvals = hseries.histogram(data1, 124, drange, drange)
    gotx, goty = hs.getData()
    assert np.all(np.isclose(hx, gotx))
    assert np.all(np.isclose(hy, goty))

    hs.setHistogramData(data2, 'data2')
    hs.autoBin     = True
    hs.ignoreZeros = False
    d2min, d2max = data2.min(), data2.max()
    drange = d2min, d2max + (d2max - d2min) / 10000.0
    nbins = hseries.autoBin(data2, drange)
    hx, hy, nvals = hseries.histogram(data2, nbins, drange, drange)
    gotx, goty = hs.getData()
    assert np.all(np.isclose(hx, gotx))
    assert np.all(np.isclose(hy, goty))

def test_ImageHistogramSeries():
    run_with_histogrampanel(_test_ImageHistogramSeries)
def _test_ImageHistogramSeries(panel, overlayList, displayCtx):
    def check(gotx, goty, img, vol):
        data = img[..., vol]
        dmin = data.min()
        dmax = data.max()
        drange = dmin, dmax + (dmax - dmin) / 10000
        nbins = hseries.autoBin(data, drange)
        expx, expy, nvals = hseries.histogram(data, nbins, drange, drange)
        assert np.all(np.isclose(gotx, expx))
        assert np.all(np.isclose(goty, expy))

    displayCtx = panel.displayCtx
    img = Image(op.join(datadir, '4d'))
    overlayList.append(img)
    opts = displayCtx.getOpts(img)
    realYield()
    hs = panel.getDataSeries(img)
    xdata, ydata = hs.getData()
    check(xdata, ydata, img, 0)
    opts.volume = 3
    realYield()
    xdata, ydata = hs.getData()
    check(xdata, ydata, img, 3)


def test_ComplexHistogramSeries():
    run_with_histogrampanel(_test_ComplexHistogramSeries)
def _test_ComplexHistogramSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    data       = np.random.randint(1, 255, (10, 10, 10)) + \
            1j * np.random.randint(1, 255, (10, 10, 10))
    data.flags.writeable = False
    data       = np.array(data, dtype=np.complex64)
    img        = Image(data, xform=np.eye(4))

    overlayList.append(img)
    realYield()
    hs               = panel.getDataSeries(img)
    hs.plotReal      = True
    hs.plotImaginary = True
    hs.plotMagnitude = True
    hs.plotPhase     = True
    his, hms, hps    = hs.extraSeries()

    real  = data.real
    imag  = data.imag
    mag   = (real ** 2 + imag ** 2) ** 0.5
    phase = np.arctan2(imag, real)

    for hdata, hhs in zip([real, imag, mag, phase],
                          [hs,   his,  hms, hps]):
        dmin, dmax = hdata.min(), hdata.max()
        drange     = dmin, dmax + (dmax - dmin) / 10000
        nbins      = hseries.autoBin(  hdata, drange)
        hx, hy, _ = hseries.histogram(hdata, nbins, drange, drange)
        gotx, goty = hhs.getData()
        assert np.all(gotx == hx)
        assert np.all(goty == hy)


def test_MeshHistogramSeries():
    run_with_histogrampanel(_test_MeshHistogramSeries)
def _test_MeshHistogramSeries(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    data = np.loadtxt(  op.join(datadir, 'mesh_l_thal_data4d.txt'))
    mesh = VTKMesh(     op.join(datadir, 'mesh_l_thal.vtk'))
    mesh.loadVertexData(op.join(datadir, 'mesh_l_thal_data4d.txt'))

    overlayList.append(mesh)
    opts = displayCtx.getOpts(mesh)
    opts.vertexData = mesh.vertexDataSets()[0]
    realYield()
    hs = panel.getDataSeries(mesh)

    def calc(d):
        dmin, dmax = d.min(), d.max()
        drange     = dmin, dmax + (dmax - dmin) / 10000
        nbins      = hseries.autoBin(  d, drange)
        dx, dy, _  = hseries.histogram(d, nbins, drange, drange)
        return dx, dy

    gotx, goty = hs.getData()
    expx, expy = calc(data[:, 0])
    assert np.all(np.isclose(gotx, expx))
    assert np.all(np.isclose(gotx, expx))

    opts.vertexDataIndex = 2
    realYield()
    gotx, goty = hs.getData()
    expx, expy = calc(data[:, 2])
    assert np.all(np.isclose(gotx, expx))
    assert np.all(np.isclose(gotx, expx))
