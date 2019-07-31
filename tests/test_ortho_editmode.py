#!/usr/bin/env python
#
# test_ortho_editmode.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import functools as ft

import numpy as np

import fsl.utils.transform as transform
import fsl.utils.idle      as   idle
from fsl.data.image  import Image
from fsl.data.bitmap import Bitmap
from fsl.data.vtk    import VTKMesh

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



def _test_editable(ortho, overlayList, displayCtx):

    # must be an image
    # must have one value per voxel (e.g. no RGB)
    # must be displayed as volume, mask, or label
    img  = Image(  op.join(datadir, '3d'))
    surf = VTKMesh(op.join(datadir, 'mesh_l_thal.vtk'))
    dti  = Image(  op.join(datadir, 'dti', 'dti_V1'))
    rgb  = Bitmap( op.join(datadir, 'test_screenshot_3d.png')).asImage()

    editable    = [(img, 'volume'),
                   (img, 'mask'),
                   (img, 'label')]
    notEditable = [(img, 'mip'),
                   (surf, 'mesh'),
                   (dti, 'rgbvector'),
                   (rgb, 'volume')]

    def setprof(profile):
        ortho.profile = profile


    savedprof = [None]

    def saveprof():
        savedprof[0] = ortho.profile

    for ovl, ot in editable:
        idle.idle(setprof, 'edit')
        idle.idle(overlayList.append, ovl, ot)
        idle.idle(displayCtx.selectOverlay, ovl)
        idle.idle(saveprof)
        idle.idle(overlayList.clear)
        idle.block(1)
        assert savedprof[0] == 'edit'

    for ovl, ot in notEditable:
        idle.idle(setprof, 'edit')
        idle.idle(overlayList.append, ovl, ot)
        idle.idle(displayCtx.selectOverlay, ovl)
        idle.idle(saveprof)
        idle.idle(overlayList.clear)
        idle.block(1)
        assert savedprof[0] == 'view'


def test_editable():
    run_with_orthopanel(_test_editable)


def _test_newMask(ortho, overlayList, displayCtx):
    img = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img]
    idle.block(0.5)
    ortho.profile = 'edit'
    idle.block(0.5)

    profile = ortho.getCurrentProfile()

    profile.createMask()
    idle.block(0.5)
    assert len(overlayList) == 2
    mask = overlayList[1]
    assert mask.sameSpace(img)
    assert np.all(mask[:] == 0)
    overlayList.remove(mask)
    idle.block(0.5)

    profile.mode = 'sel'
    idle.block(0.5)
    ed = profile.editor(img)
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(0.5)
    profile.createMask()
    idle.block(0.5)
    assert len(overlayList) == 2
    mask = overlayList[1]
    assert mask.sameSpace(img)
    exp = np.zeros(mask.shape)
    exp[8:12, 8:12, 8:12] = 1
    assert np.all(mask[:] == exp)
    overlayList[:] = []
    idle.block(0.55)


def test_newMask():
    run_with_orthopanel(_test_newMask)


def _test_SelectionActions(ortho, overlayList, displayCtx):
    img1 = Image(np.random.randint(1, 65536, (20, 20, 20)))
    img2 = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img1, img2]
    displayCtx.selectOverlay(img1)
    idle.block(0.25)
    ortho.profile = 'edit'
    idle.block(0.25)
    profile = ortho.getCurrentProfile()
    profile.mode = 'sel'
    profile.drawMode = False
    idle.block(0.25)
    ed = profile.editor(img1)

    # clear
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(0.25)
    profile.clearSelection()
    assert np.all(ed.getSelection().getSelection() == 0)

    # fill
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(0.25)
    profile.fillValue = 999
    profile.fillSelection()
    exp = np.copy(img1[:])
    exp[8:12, 8:12, 8:12] = 999
    assert np.all(img1[:] == exp)

    # erase
    profile.clearSelection()
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(3, 3, 3))
    idle.block(0.25)
    profile.eraseValue = -999
    profile.eraseSelection()
    exp = np.copy(img1[:])
    exp[3:7, 3:7, 3:7] = -999
    assert np.all(img1[:] == exp)

    # invert
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(0.25)
    profile.invertSelection()
    exp = np.ones(img1.shape)
    exp[8:12, 8:12, 8:12] = 0
    assert np.all(ed.getSelection().getSelection() == exp)

    # copy+paste
    profile.clearSelection()
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    displayCtx.selectOverlay(img2)
    profile.copySelection()
    displayCtx.selectOverlay(img1)
    idle.block(0.25)
    profile.pasteSelection()
    idle.block(0.25)
    exp = np.copy(img1[:])
    exp[8:12, 8:12, 8:12] = img2[8:12, 8:12, 8:12]
    assert np.all(img1[:] == exp)



def test_SelectionActions():
    run_with_orthopanel(_test_SelectionActions)
