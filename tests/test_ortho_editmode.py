#!/usr/bin/env python
#
# test_ortho_editmode.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import functools as ft

import numpy as np

import wx

import fsl.utils.transform as transform
from fsl.data.image import Image

from . import run_with_orthopanel, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_fillSelection(ortho, overlayList, displayCtx, img, canvas=None):

    if canvas is None: cidx = 2
    else:              cidx = canvas

    overlayList.append(img)
    realYield()
    displayCtx.displaySpace  = img
    displayCtx.worldLocation = transform.transform([0, 0, 0], img.
                                                   voxToWorldMat)
    realYield()
    ortho.profile = 'edit'
    realYield(20)

    profile = ortho.getCurrentProfile()
    profile.mode          = 'sel'
    profile.drawMode      = False
    profile.selectionSize = 1
    profile.fillValue     = 999

    canvas = ortho.getGLCanvases()[cidx]
    opts   = ortho.displayCtx.getOpts(img)

    realYield(20)

    if   cidx == 0: xidx, yidx = 1, 2
    elif cidx == 1: xidx, yidx = 0, 2
    elif cidx == 2: xidx, yidx = 0, 1

    pxs = np.random.randint(0, img.shape[xidx], 10)
    pys = np.random.randint(0, img.shape[yidx], 10)

    for i in range(10):
        px, py   = pxs[i], pys[i]
        pt       = [None, None, None]
        pt[xidx] = px
        pt[yidx] = py
        pt[cidx] = 0
        pos      = opts.transformCoords(pt, 'voxel', 'display')

        px, py = pos[xidx], pos[yidx]

        bounds = canvas.opts.displayBounds

        xoff = bounds.xlo - opts.bounds.ylo
        yoff = bounds.ylo - opts.bounds.zlo

        px = (px - xoff) / bounds.xlen
        py = (py - yoff) / bounds.ylen

        profile._selModeLeftMouseDown(None, canvas, (1 - px, py), pos)
        realYield(5)
        profile._selModeLeftMouseUp(None, canvas, (1 - px, py), pos)
        realYield(5)

    sel = np.array(profile.editor(img).getSelection().getSelection())

    profile.fillSelection()
    realYield(20)

    w, h = canvas.GetClientSize().Get()

    voxels = np.zeros((10, 3), dtype=np.int32)
    voxels[:, xidx] = pxs
    voxels[:, yidx] = pys
    voxels[:, cidx] = 0

    xs, ys, zs = voxels.T

    exp             = np.zeros(img.shape)
    exp[xs, ys, zs] = 1

    assert np.all(sel == exp)
    assert np.all(img[:][xs, ys, zs] == 999)

    overlayList[:] = []



def test_fillSelection():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=0)
    run_with_orthopanel(tfs)
    tfs = ft.partial(_test_fillSelection, img=img, canvas=1)
    run_with_orthopanel(tfs)
    tfs = ft.partial(_test_fillSelection, img=img, canvas=2)
    run_with_orthopanel(tfs)


def test_fillSelection_2d():
    img = Image(np.random.randint(1, 65536, (60, 60, 1)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=2)
    run_with_orthopanel(tfs)
    img.save('one')

    img = Image(np.random.randint(1, 65536, (60, 1, 60)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=1)
    run_with_orthopanel(tfs)
    img.save('two')

    img = Image(np.random.randint(1, 65536, (1, 60, 60)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=0)
    run_with_orthopanel(tfs)
    img.save('three')
