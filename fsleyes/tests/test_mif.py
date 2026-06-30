#!/usr/bin/env python
#
# test_mif.py - Test the MIFImage overlay
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

from fsleyes.data.mif import MIFImage
from fsl.data.image   import Image


def test_mif_3d():
    datadir = op.join(op.dirname(__file__), 'testdata')

    benchmarkfile = f'{datadir}/3d.nii.gz'
    testfile      = f'{datadir}/3d.mif'
    bmimg         = Image(benchmarkfile)
    testimg       = MIFImage(testfile)

    assert np.all(np.isclose(bmimg.data, testimg.data))
    assert testimg.sameSpace(bmimg)


def test_mif_4d():
    datadir = op.join(op.dirname(__file__), 'testdata')

    benchmarkfile = f'{datadir}/4d.nii.gz'
    bmimg         = Image(benchmarkfile)

    testfiles = [f'{datadir}/4d.mif',
                 f'{datadir}/4d_time_fastest_changing.mif']

    for testfile in testfiles:
        testimg = MIFImage(testfile)

        assert np.all(np.isclose(bmimg.data, testimg.data))
        assert testimg.sameSpace(bmimg)
