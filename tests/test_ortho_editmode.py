#!/usr/bin/env python
#
# test_ortho_editmode.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import functools as ft

import nibabel as nib
import numpy as np

import fsl.transform.affine as affine
import fsl.utils.idle       as  idle
from fsl.data.image  import Image
from fsl.data.bitmap import Bitmap
from fsl.data.vtk    import VTKMesh

from . import run_with_orthopanel, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_fillSelection(ortho, overlayList, displayCtx, img, canvas=None, vol=None):

    if canvas is None: cidx = 2
    else:              cidx = canvas

    if vol is None:
        vol = 0

    overlayList.append(img, volume=vol)
    realYield()
    displayCtx.displaySpace  = img
    displayCtx.worldLocation = affine.transform([0, 0, 0], img.
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

    exp             = np.zeros(img.shape[:3])
    exp[xs, ys, zs] = 1

    assert np.all(sel == exp)

    if len(img.shape) == 3:
        assert np.all(img[:][xs, ys, zs] == 999)
    elif len(img.shape) == 4:
        vol = displayCtx.getOpts(img).volume
        assert np.all(img[:][xs, ys, zs, vol] == 999)

    overlayList[:] = []


def test_fillSelection_x():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=0)
    run_with_orthopanel(tfs)


def test_fillSelection_y():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=1)
    run_with_orthopanel(tfs)


def test_fillSelection_z():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=2)
    run_with_orthopanel(tfs)


def test_fillSelection_2d_x():
    img = Image(np.random.randint(1, 65536, (60, 60, 1)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=2)
    run_with_orthopanel(tfs)


def test_fillSelection_2d_y():
    img = Image(np.random.randint(1, 65536, (60, 1, 60)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=1)
    run_with_orthopanel(tfs)


def test_fillSelection_2d_z():
    img = Image(np.random.randint(1, 65536, (1, 60, 60)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=0)
    run_with_orthopanel(tfs)


def test_fillSelection_4d_x():
    img = Image(np.random.randint(1, 65536, (40, 40, 40, 10)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=0)
    run_with_orthopanel(tfs)

def test_fillSelection_4d_y():
    img = Image(np.random.randint(1, 65536, (40, 40, 40, 10)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=1, vol=3)
    run_with_orthopanel(tfs)


def test_fillSelection_4d_z():
    img = Image(np.random.randint(1, 65536, (40, 40, 40, 10)))
    tfs = ft.partial(_test_fillSelection, img=img, canvas=2, vol=8)
    run_with_orthopanel(tfs)


def _test_editable(ortho, overlayList, displayCtx, ovl, ovlType, editable):

    # must be an image
    # must have one value per voxel (e.g. no RGB)
    # must be displayed as volume, mask, or label

    if editable: expect = 'edit'
    else:        expect = 'view'

    def setprof(profile):
        ortho.profile = profile

    savedprof = [None]

    def saveprof():
        savedprof[0] = ortho.profile

    idle.idle(setprof, 'edit')
    idle.idle(overlayList.append, ovl, overlayType=ovlType)
    idle.idle(displayCtx.selectOverlay, ovl)
    idle.block(3)
    idle.idle(saveprof)
    idle.idle(overlayList.clear)
    idle.block(3)
    assert savedprof[0] == expect


def test_editable_volume():
    img  = Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_editable, img, 'volume', True)


def test_editable_mask():
    img  = Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_editable, img, 'mask', True)


def test_editable_label():
    img  = Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_editable, img, 'label', True)


def test_notEditable_mip():
    img  = Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_editable, img, 'mip', False)


def test_notEditable_mesh():
    surf = VTKMesh(op.join(datadir, 'mesh_l_thal.vtk'))
    run_with_orthopanel(_test_editable, surf, 'mesh', False)


def test_notEditable_rgbvector():
    dti  = Image(  op.join(datadir, 'dti', 'dti_V1'))
    run_with_orthopanel(_test_editable, dti, 'rgbvector', False)


def test_notEditable_rgbvolume():
    rgb  = Bitmap( op.join(datadir, 'test_screenshot_3d.png')).asImage()
    run_with_orthopanel(_test_editable, rgb, 'rgbvector', False)


def _test_newMask(ortho, overlayList, displayCtx):
    img = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img]
    idle.block(2.5)
    ortho.profile = 'edit'
    idle.block(2.5)

    profile = ortho.getCurrentProfile()

    profile.createMask()
    idle.block(2.5)
    assert len(overlayList) == 2
    mask = overlayList[1]
    assert mask.sameSpace(img)
    assert np.all(mask[:] == 0)
    overlayList.remove(mask)
    idle.block(2.5)

    profile.mode = 'sel'
    idle.block(2.5)
    ed = profile.editor(img)
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2.5)
    profile.createMask()
    idle.block(2.5)
    assert len(overlayList) == 2
    mask = overlayList[1]
    assert mask.sameSpace(img)
    exp = np.zeros(mask.shape)
    exp[8:12, 8:12, 8:12] = 1
    assert np.all(mask[:] == exp)
    overlayList[:] = []
    idle.block(2.5)


def test_newMask():
    run_with_orthopanel(_test_newMask)


def _test_SelectionActions(ortho, overlayList, displayCtx):
    img1 = Image(np.random.randint(1, 65536, (20, 20, 20)))
    img2 = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img1, img2]
    displayCtx.selectOverlay(img1)
    idle.block(2)
    ortho.profile = 'edit'
    idle.block(2)
    profile = ortho.getCurrentProfile()
    profile.mode = 'sel'
    profile.drawMode = False
    idle.block(2)
    ed = profile.editor(img1)

    # clear
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2)
    profile.clearSelection()
    assert np.all(ed.getSelection().getSelection() == 0)

    # fill
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2)
    profile.fillValue = 999
    profile.fillSelection()
    exp = np.copy(img1[:])
    exp[8:12, 8:12, 8:12] = 999
    assert np.all(img1[:] == exp)

    # erase
    profile.clearSelection()
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(3, 3, 3))
    idle.block(2)
    profile.eraseValue = -999
    profile.eraseSelection()
    exp = np.copy(img1[:])
    exp[3:7, 3:7, 3:7] = -999
    assert np.all(img1[:] == exp)

    # invert
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2)
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
    idle.block(2)
    profile.pasteSelection()
    idle.block(2)
    exp = np.copy(img1[:])
    exp[8:12, 8:12, 8:12] = img2[8:12, 8:12, 8:12]
    assert np.all(img1[:] == exp)



def test_SelectionActions():
    run_with_orthopanel(_test_SelectionActions)


# regression - draw selection would crash
# for 4D image with small pixdim4 (fixed
# in (!196)
def test_applySelection_small_pixdim4():
    run_with_orthopanel(_test_applySelection_small_pixdim4)

def _test_applySelection_small_pixdim4(ortho, overlayList, displayCtx):
    data = np.random.random((10, 10, 10, 10))
    img = nib.Nifti1Image(data, np.eye(4))
    img.header.set_zooms((1, 1, 1, 0.1))
    img = Image(img)

    overlayList.append(img)
    realYield()
    displayCtx.displaySpace  = img
    realYield()

    ortho.profile = 'edit'
    realYield(20)

    profile = ortho.getCurrentProfile()
    profile.mode          = 'sel'
    profile.drawMode      = False
    profile.selectionSize = 1

    realYield(20)

    canvas = ortho.getGLCanvases()[0]
    opts   = ortho.displayCtx.getOpts(img)

    pos        = opts.transformCoords([5, 5, 5], 'voxel', 'display')
    px, py     = pos[1], pos[2]

    bounds = canvas.opts.displayBounds

    xoff = bounds.xlo - opts.bounds.ylo
    yoff = bounds.ylo - opts.bounds.zlo
    px   = (px - xoff) / bounds.xlen
    py   = (py - yoff) / bounds.ylen

    profile._selModeLeftMouseDown(None, canvas, (1 - px, py), pos)
    realYield(20)
    profile._selModeLeftMouseUp(None, canvas, (1 - px, py), pos)
    realYield(20)

    sel = np.array(profile.editor(img).getSelection().getSelection())
    exp = np.zeros((10, 10, 10))
    exp[5, 5, 5] = 1

    assert np.all(sel == exp)

    overlayList[:] = []
