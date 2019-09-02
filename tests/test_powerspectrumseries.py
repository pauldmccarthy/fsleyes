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

from . import run_with_powerspectrumpanel, realYield


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
        got1 = psseries.calcPowerSpectrum(data)
        got2 = psseries.calcPowerSpectrum(data, True)

        assert got1.shape == (explen,)
        assert got2.shape == (explen,)
        assert np.issubdtype(got1.dtype, expdtype)
        assert np.issubdtype(got2.dtype, expdtype)


def test_calcFrequencies():

    # (data, explen)
    tests = [
        (np.random.random(99),                               49),
        (np.random.random(100),                              50),
        (np.random.random(99)  + np.random.random(99)  * 1j, 99),
        (np.random.random(100) + np.random.random(100) * 1j, 100),
    ]

    for data, explen in tests:
        got = psseries.calcFrequencies(data, 1)
        assert got.shape == (explen,)


def test_magnitude():
    assert np.isclose(psseries.magnitude(3 + 4j), 5.0)


def test_phase():
    assert np.isclose(psseries.phase(4 + 4j), np.pi / 4)


def test_VoxelPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_VoxelPowerSpectrumSeries)

def _test_VoxelPowerSpectrumSeries(panel, overlayList, displayCtx):
    pass


def test_ComplexPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_ComplexPowerSpectrumSeries)

def _test_ComplexPowerSpectrumSeries(panel, overlayList, displayCtx):
    pass


def test_MelodicPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_MelodicPowerSpectrumSeries)

def _test_MelodicPowerSpectrumSeries(panel, overlayList, displayCtx):
    pass


def test_MeshPowerSpectrumSeries():
    run_with_powerspectrumpanel(_test_MeshPowerSpectrumSeries)

def _test_MeshPowerSpectrumSeries(panel, overlayList, displayCtx):
    pass
