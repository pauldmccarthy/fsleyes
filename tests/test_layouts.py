#!/usr/bin/env python
#
# test_layouts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import fsl.data.image as fslimage

import fsleyes.layouts as layouts

from . import run_with_fsleyes, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_layout(frame, overlayList, displayCtx, layout):
    img = fslimage.Image(op.join(datadir, '4d'))
    overlayList.append(img)
    layouts.loadLayout(frame, layout)
    realYield(100)


def test_default():
    run_with_fsleyes(_test_layout, 'default')


def test_ortho():
    run_with_fsleyes(_test_layout, 'ortho')


def test_lightbox():
    run_with_fsleyes(_test_layout, 'lightbox')


def test_3d():
    run_with_fsleyes(_test_layout, '3d')


def test_melodic():
    run_with_fsleyes(_test_layout, 'melodic')


def test_feat():
    run_with_fsleyes(_test_layout, 'feat')
