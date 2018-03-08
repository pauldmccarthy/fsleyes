#!/usr/bin/env python
#
# test_perspectives.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import fsl.data.image as fslimage

import fsleyes.perspectives as perspectives

from . import run_with_fsleyes, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_perspective(frame, overlayList, displayCtx, persp):
    img = fslimage.Image(op.join(datadir, '4d'))
    overlayList.append(img)
    perspectives.loadPerspective(frame, persp)
    realYield(100)


def test_default():
    run_with_fsleyes(_test_perspective, 'default')


def test_ortho():
    run_with_fsleyes(_test_perspective, 'ortho')


def test_lightbox():
    run_with_fsleyes(_test_perspective, 'lightbox')


def test_3d():
    run_with_fsleyes(_test_perspective, '3d')


def test_melodic():
    run_with_fsleyes(_test_perspective, 'melodic')


def test_feat():
    run_with_fsleyes(_test_perspective, 'feat')
