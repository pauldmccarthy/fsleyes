#!/usr/bin/env python
#
# test_projectimagetosurface.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
from unittest import mock

import wx
import numpy as np

from fsleyes.tests import run_with_orthopanel

import fsl.data.image       as fslimage
import fsl.data.vtk         as fslvtk
import fsl.transform.affine as affine

import fsleyes.plugins.tools.projectimagetosurface as pits


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def _generate_test_data():
    image = fslimage.Image(op.join(datadir, 'mesh_ref.nii.gz'))
    mesh  = fslvtk.VTKMesh(op.join(datadir, 'mesh_l_thal.vtk'))

    # the mesh is defined in terms of
    # scaled voxels; let's put it into
    # world coordinates so we can more
    # easily test different overlap
    # scenarios
    verts = affine.transform(mesh.vertices, image.getAffine('fsl', 'world'))
    mesh.addVertices(verts, 'world')

    # create a couple of other ref
    # images which overlap with the
    # mesh to varying amounts
    v2w        = image.getAffine('voxel', 'world')
    some_xform = affine.concat(affine.scaleOffsetXform(1, 15), v2w)
    none_xform = affine.concat(affine.scaleOffsetXform(1, 50), v2w)
    image_all  = fslimage.Image(image.data, xform=v2w,        name='all')
    image_some = fslimage.Image(image.data, xform=some_xform, name='some')
    image_none = fslimage.Image(image.data, xform=none_xform, name='none')

    return mesh, image_all, image_some, image_none



def test_projectimagetosurface():
    run_with_orthopanel(_test_projectimagetosurface)


def _test_projectimagetosurface(panel, overlayList, displayCtx):

    frame      = panel.GetTopLevelParent()
    displayCtx = panel.displayCtx

    mesh, image_all, image_some, image_none = _generate_test_data()

    act = pits.ProjectImageToSurfaceAction(
        overlayList, frame.displayCtx, frame)

    overlayList[:] = [mesh]

    # Test that the action exits early
    # if no suitable images loaded
    class MockMsgDlg:
        def __init__(self):
            self.called = False
        def __call__(self, *args, **kwargs):
            self.called = True
            return self
        def ShowModal(self):
            pass

    dlg = MockMsgDlg()
    with mock.patch('wx.MessageDialog', dlg):
        act()
    assert dlg.called

    # image loaded, but doesn't overlap
    # with mesh - exit early
    dlg.called = False
    overlayList.append(image_none)
    displayCtx.selectOverlay(mesh)
    with mock.patch('wx.MessageDialog', dlg):
        act()
    assert dlg.called

    # Suitable images loaded - test
    # selection and projection
    overlayList.extend([image_all, image_some])
    displayCtx.selectOverlay(mesh)

    mopts            = displayCtx.getOpts(mesh)
    mopts.coordSpace = 'affine'
    mopts.refImage   = image_all

    class MockChoiceDlg:
        def __init__(self):
            self.choices   = None
            self.retval    = wx.ID_OK
            self.selection = None
        def __call__(self, *args, choices=None, **kwargs):
            self.choices = choices
            return self
        def ShowModal(self):
            return self.retval
        def GetSelection(self):
            return self.selection

    # cancel
    dlg = MockChoiceDlg()
    dlg.retval = wx.ID_CANCEL
    with mock.patch('wx.SingleChoiceDialog', dlg):
        act()
    assert dlg.choices == ['all', 'some']
    assert mesh.vertexDataSets() == []

    dlg.retval    = wx.ID_OK
    dlg.selection = 0
    with mock.patch('wx.SingleChoiceDialog', dlg):
        act()
    assert mesh.vertexDataSets() == ['all']
    assert mopts.vertexData      == 'all'

    dlg.retval    = wx.ID_OK
    dlg.selection = 1
    with mock.patch('wx.SingleChoiceDialog', dlg):
        act()
    assert mesh.vertexDataSets() == ['all', 'some']
    assert mopts.vertexData      == 'some'

    dlg.retval    = wx.ID_OK
    dlg.selection = 0
    with mock.patch('wx.SingleChoiceDialog', dlg):
        act()
    assert mesh.vertexDataSets() == ['all', 'some', 'all [1]']
    assert mopts.vertexData      == 'all [1]'


def test_projectImageDataOntoMesh():
    run_with_orthopanel(_test_projectImageDataOntoMesh)
def _test_projectImageDataOntoMesh(panel, overlayList, displayCtx):

    displayCtx = panel.displayCtx
    mesh, image_all, image_some, image_none = _generate_test_data()

    overlayList.extend((mesh, image_all, image_some, image_none))
    mopts            = displayCtx.getOpts(mesh)
    mopts.coordSpace = 'affine'
    mopts.refImage   = image_all

    vdall  = pits.projectImageDataOntoMesh(displayCtx, image_all,  mesh)
    vdsome = pits.projectImageDataOntoMesh(displayCtx, image_some, mesh)
    vdnone = pits.projectImageDataOntoMesh(displayCtx, image_none, mesh)

    assert     np.all(np.isfinite(vdall))
    assert     np.isfinite(vdsome).sum() > 0
    assert not np.all(np.isfinite(vdnone))



def test_overlap():

    # (bbox1, bbox2, expected)
    tests = [
        ([(0, 1)], [(2,    3)],    False),
        ([(0, 1)], [(0.5,  1.5)],  True),
        ([(0, 1)], [(0.25, 0.75)], True),
        ([(0, 1)], [(-1,   2)],    True),
        ([(0, 1)], [(-1,   0.5)],  True),
        ([(0, 1)], [(-2,  -1)],    False),
    ]

    for box1, box2, exp in tests:
        assert pits.overlap(box1, box2) == exp
