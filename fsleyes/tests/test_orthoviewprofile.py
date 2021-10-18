#!/usr/bin/env python

import os.path as op

from fsl.data.image import Image


from fsleyes.tests import run_with_orthopanel, realYield, mockMouseEvent


datadir = op.join(op.dirname(__file__), 'testdata')


def test_regionBriconMode():
    run_with_orthopanel(_test_regionBriconMode)
def _test_regionBriconMode(ortho, overlayList, displayCtx):

    img = Image(op.join(datadir, '3d'))
    overlayList.append(img)

    realYield()

    opts     = ortho.displayCtx.getOpts(img)
    profile  = ortho.currentProfile
    zcanvas  = ortho.getGLCanvases()[2]
    z        = int(opts.transformCoords([displayCtx.location],
                                        'display',
                                        'voxel',
                                        vround=True)[0, 2])

    vstart = [ 3,  3,  z]
    vend   = [ 10, 10, z]
    dstart = opts.transformCoords(vstart, 'voxel', 'display')
    dend   = opts.transformCoords(vend,   'voxel', 'display')

    profile.mode = 'regionBricon'

    mockMouseEvent(profile, zcanvas, 'LeftMouseDown', dstart)
    mockMouseEvent(profile, zcanvas, 'LeftMouseDrag', dstart)
    mockMouseEvent(profile, zcanvas, 'LeftMouseUp',   dend)

    realYield()

    sx, sy, sz = vstart
    ex, ey, ez = vend

    data = img.data[sx:ex + 1, sy:ey + 1, sz:ez + 1]
    dmin = data.min()
    dmax = data.max()

    assert opts.displayRange == (dmin, dmax)
