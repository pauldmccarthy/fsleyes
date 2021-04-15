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

from fsleyes.profiles.orthoviewprofile import OrthoViewProfile
from fsleyes.profiles.orthoeditprofile import OrthoEditProfile

from fsleyes.tests import run_with_orthopanel, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_select_and_fill(
        ortho, overlayList, displayCtx, img, canvas=None, vol=None):

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

    ortho.profileManager.activateProfile(OrthoEditProfile)
    realYield(20)

    profile = ortho.currentProfile
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


def _test_select_and_fill_x():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=0)
    run_with_orthopanel(tfs)


def test_select_and_fill_y():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=1)
    run_with_orthopanel(tfs)


def test_select_and_fill_z():
    img = Image(op.join(datadir, '3d'))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=2)
    run_with_orthopanel(tfs)


def test_select_and_fill_2d_x():
    img = Image(np.random.randint(1, 65536, (60, 60, 1)))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=2)
    run_with_orthopanel(tfs)


def test_select_and_fill_2d_y():
    img = Image(np.random.randint(1, 65536, (60, 1, 60)))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=1)
    run_with_orthopanel(tfs)


def test_select_and_fill_2d_z():
    img = Image(np.random.randint(1, 65536, (1, 60, 60)))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=0)
    run_with_orthopanel(tfs)


def test_select_and_fill_4d_x():
    img = Image(np.random.randint(1, 65536, (40, 40, 40, 10)))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=0)
    run_with_orthopanel(tfs)

def test_select_and_fill_4d_y():
    img = Image(np.random.randint(1, 65536, (40, 40, 40, 10)))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=1, vol=3)
    run_with_orthopanel(tfs)


def test_select_and_fill_4d_z():
    img = Image(np.random.randint(1, 65536, (40, 40, 40, 10)))
    tfs = ft.partial(_test_select_and_fill, img=img, canvas=2, vol=8)
    run_with_orthopanel(tfs)


def _test_editable(ortho, overlayList, displayCtx, ovl, ovlType, editable):

    # must be an image
    # must have one value per voxel (e.g. no RGB)
    # must be displayed as volume, mask, or label

    idle.idle(overlayList.append, ovl, overlayType=ovlType)
    idle.idle(displayCtx.selectOverlay, ovl)
    idle.block(3)

    try:
        ortho.toggleEditMode()
        assert editable
    except Exception:
        assert not editable

    if editable: expect = OrthoEditProfile
    else:        expect = OrthoViewProfile

    assert isinstance(ortho.currentProfile, expect)
    idle.idle(overlayList.clear)
    idle.block(3)
    assert isinstance(ortho.currentProfile, OrthoViewProfile)


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
    run_with_orthopanel(_test_editable, rgb, 'volume', False)


def test_newMask():
    run_with_orthopanel(_test_newMask)

def _test_newMask(ortho, overlayList, displayCtx):
    img = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img]
    idle.block(2.5)
    ortho.profileManager.activateProfile(OrthoEditProfile)
    idle.block(2.5)

    profile = ortho.currentProfile

    profile.createMask()
    idle.block(2.5)
    assert len(overlayList) == 2
    mask = overlayList[1]
    assert mask.sameSpace(img)
    assert np.all(mask[:] == 0)


def test_newMask_with_selection():
    run_with_orthopanel(_test_newMask_with_selection)

def _test_newMask_with_selection(ortho, overlayList, displayCtx):
    img = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img]
    idle.block(2.5)
    ortho.profileManager.activateProfile(OrthoEditProfile)
    idle.block(2.5)

    profile = ortho.currentProfile

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


def _setup_selectionAction_test(ortho, overlayList, displayCtx):
    img1 = Image(np.random.randint(1, 65536, (20, 20, 20)))
    img2 = Image(np.random.randint(1, 65536, (20, 20, 20)))
    overlayList[:] = [img1, img2]
    displayCtx.selectOverlay(img1)
    idle.block(2)
    ortho.profileManager.activateProfile(OrthoEditProfile)
    idle.block(2)
    profile = ortho.currentProfile
    profile.mode = 'sel'
    profile.drawMode = False
    idle.block(2)


def test_clearSelection():
    run_with_orthopanel(_test_clearSelection)

def _test_clearSelection(ortho, overlayList, displayCtx):
    _setup_selectionAction_test(ortho, overlayList, displayCtx)
    img1 = overlayList[0]
    profile = ortho.currentProfile
    ed = profile.editor(img1)

    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2)
    profile.clearSelection()
    assert np.all(ed.getSelection().getSelection() == 0)


def test_fillSelection():
    run_with_orthopanel(_test_fillSelection)

def _test_fillSelection(ortho, overlayList, displayCtx):

    _setup_selectionAction_test(ortho, overlayList, displayCtx)
    img1 = overlayList[0]
    profile = ortho.currentProfile
    ed = profile.editor(img1)

    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2)
    profile.fillValue = 999
    profile.fillSelection()
    idle.block(1)
    exp = np.copy(img1[:])
    exp[8:12, 8:12, 8:12] = 999
    assert np.all(img1[:] == exp)


def test_eraseSelection():
    run_with_orthopanel(_test_eraseSelection)

def _test_eraseSelection(ortho, overlayList, displayCtx):

    _setup_selectionAction_test(ortho, overlayList, displayCtx)
    img1 = overlayList[0]
    profile = ortho.currentProfile
    ed = profile.editor(img1)

    # erase
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(3, 3, 3))
    idle.block(2)
    profile.eraseValue = -999
    profile.eraseSelection()
    idle.block(1)
    exp = np.copy(img1[:])
    exp[3:7, 3:7, 3:7] = -999
    assert np.all(img1[:] == exp)


def test_invertSelection():
    run_with_orthopanel(_test_invertSelection)

def _test_invertSelection(ortho, overlayList, displayCtx):

    _setup_selectionAction_test(ortho, overlayList, displayCtx)
    img1 = overlayList[0]
    profile = ortho.currentProfile
    ed = profile.editor(img1)

    # invert
    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    idle.block(2)
    profile.invertSelection()
    exp = np.ones(img1.shape)
    exp[8:12, 8:12, 8:12] = 0
    assert np.all(ed.getSelection().getSelection() == exp)


def test_copyPasteData():
    run_with_orthopanel(_test_copyPasteData)

def _test_copyPasteData(ortho, overlayList, displayCtx):

    _setup_selectionAction_test(ortho, overlayList, displayCtx)
    img1, img2 = overlayList[:]
    profile = ortho.currentProfile
    ed = profile.editor(img1)

    ed.getSelection().addToSelection(np.ones((4, 4, 4)), offset=(8, 8, 8))
    displayCtx.selectOverlay(img2)
    profile.copyPasteData()
    displayCtx.selectOverlay(img1)
    idle.block(2)
    profile.copyPasteData()
    idle.block(2)
    exp = np.copy(img1[:])
    exp[8:12, 8:12, 8:12] = img2[8:12, 8:12, 8:12]
    assert np.all(img1[:] == exp)
    profile.copyPasteData(clear=True)


def test_copyPasteSelection():
    run_with_orthopanel(_test_copyPasteSelection)

def _test_copyPasteSelection(ortho, overlayList, displayCtx):

    _setup_selectionAction_test(ortho, overlayList, displayCtx)
    displayCtx = ortho.displayCtx
    img1 = overlayList[0]
    opts = displayCtx.getOpts(img1)
    profile = ortho.currentProfile
    ed = profile.editor(img1)

    ortho.getXCanvas().SetFocus()
    displayCtx.location = opts.transformCoords((8, 8, 8), 'voxel', 'display')
    idle.block(0.5)
    ed.getSelection().addToSelection(np.ones((1, 4, 4)), offset=(8, 8, 8))
    idle.block(0.5)
    profile.copyPasteSelection()
    idle.block(0.5)
    displayCtx.location = opts.transformCoords((9, 8, 8), 'voxel', 'display')
    idle.block(0.5)
    profile.copyPasteSelection()
    idle.block(0.5)
    displayCtx.location = opts.transformCoords((10, 8, 8), 'voxel', 'display')
    idle.block(0.5)
    profile.copyPasteSelection()
    idle.block(0.5)

    exp = np.zeros(img1.shape[:3])
    exp[8:11, 8:12, 8:12] = 1
    assert np.all(ed.getSelection().getSelection() == exp)


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

    ortho.profileManager.activateProfile(OrthoEditProfile)
    realYield(20)

    profile = ortho.currentProfile
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
