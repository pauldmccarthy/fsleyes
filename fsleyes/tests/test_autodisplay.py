#!/usr/bin/env python
#
# test_autodisplay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op
import numpy as np

import fsl.data.image as fslimage

import fsl.data.utils               as dutils

from fsleyes.actions.applycommandline import applyCommandLineArgs

from fsleyes.tests import run_with_fsleyes, tempdir, touch, realYield


def random_image(shape=(10, 10, 10)):
    data = np.random.random((10, 10, 10))
    return fslimage.Image(data, xform=np.eye(4))


def create_melodic_dir():
    mdir = 'filtered_func_data.ica'
    os.mkdir(mdir)
    random_image((10, 10, 10, 10)).save(op.join(mdir, 'melodic_IC'))
    random_image((10, 10, 10))    .save(op.join(mdir, 'mean'))
    np.savetxt(op.join(mdir, 'melodic_mix'),   np.random.random((10, 10)))
    np.savetxt(op.join(mdir, 'melodic_FTmix'), np.random.random((10, 10)))
    return mdir


def test_melodic_IC():
    run_with_fsleyes(_test_melodic_IC)


def _test_melodic_IC(frame, overlayList, displayCtx):

    loaded = [False]

    def onLoad(*_):
        loaded[0] = True

    with tempdir():

        mdir = op.abspath(create_melodic_dir())
        mean = op.join(mdir, 'mean.nii.gz')
        mic  = op.join(mdir, 'melodic_IC.nii.gz')

        applyCommandLineArgs(overlayList, displayCtx, ['-ad', mdir],
                             onLoad=onLoad)

        while not loaded[0]:
            realYield()

        assert len(overlayList)                == 2
        assert overlayList[0].dataSource       == mean
        assert overlayList[1].dataSource       == mic
        assert displayCtx.getSelectedOverlay() is overlayList[1]
