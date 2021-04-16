#!/usr/bin/env python


import os.path as op

from fsl.data.image import Image

from fsleyes.tests import run_with_fsleyes, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def test_overlayList_initProps():
    run_with_fsleyes(_test_overlayList_initProps)


def _test_overlayList_initProps(frame, overlayList, displayCtx):

    img = Image(op.join(datadir, '3d'))

    overlayList.append(img,
                       overlayType='mask',
                       alpha=75,
                       invert=True,
                       colour=(0.5, 0.2, 0.3))

    realYield()

    assert overlayList[0] is img

    display = displayCtx.getDisplay(img)
    opts    = displayCtx.getOpts(   img)

    assert display.overlayType == 'mask'
    assert display.alpha       == 75
    assert opts.invert
    assert list(opts.colour)   == [0.5, 0.2, 0.3, 1.0]
