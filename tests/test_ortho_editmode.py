#!/usr/bin/env python
#
# test_ortho_editmode.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

import wx

from fsl.data.image import Image

from . import run_with_orthopanel, realYield, simclick


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_fillSelection(ortho, overlayList, displayCtx):
    sim = wx.UIActionSimulator()
    img = Image(op.join(datadir, '3d'))
    overlayList.append(img)
    realYield()
    ortho.profile = 'edit'
    realYield(20)

    profile = ortho.getCurrentProfile()
    profile.mode          = 'sel'
    profile.drawMode      = False
    profile.selectionSize = 1
    profile.fillValue     = 999

    xcanvas = ortho.getXCanvas()
    opts    = ortho.displayCtx.getOpts(img)

    realYield(20)

    pxs = np.random.randint(0, img.shape[1], 10)
    pys = np.random.randint(0, img.shape[2], 10)

    for i in range(10):
        px, py = pxs[i] + 0.5, pys[i] + 0.5
        pos    = opts.transformCoords((8, px, py), 'voxel', 'display')

        px, py = pos[1], pos[2]

        bounds = xcanvas.opts.displayBounds

        xoff = bounds.xlo - opts.bounds.ylo
        yoff = bounds.ylo - opts.bounds.zlo

        px = (px - xoff) / bounds.xlen
        py = (py - yoff) / bounds.ylen

        simclick(sim, xcanvas, pos=(px, 1 - py))
        realYield(10)

    sel = np.array(profile.editor(img).getSelection().getSelection())

    profile.fillSelection()
    realYield(20)

    w, h = xcanvas.GetClientSize().Get()

    voxels = np.zeros((10, 3), dtype=np.int32)
    voxels[:, 0] = 8
    voxels[:, 1] = pxs
    voxels[:, 2] = pys

    xs, ys, zs = voxels.T

    exp             = np.zeros(img.shape)
    exp[xs, ys, zs] = 1

    assert np.all(sel == exp)
    assert np.all(img[:][xs, ys, zs] == 999)



def test_fillSelection():
    run_with_orthopanel(_test_fillSelection)
