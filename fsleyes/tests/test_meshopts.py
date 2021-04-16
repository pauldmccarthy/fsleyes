#!/usr/bin/env python

import itertools as it
import os.path as op

import numpy as np

import fsleyes.displaycontext.meshopts as meshopts

import fsl.data.image as fslimage
import fsl.data.vtk   as fslvtk
import fsl.utils.image.resample as resample

from fsleyes.tests import run_with_orthopanel


datadir  = op.join(op.dirname(__file__), 'testdata')


def test_transformCoords():
    run_with_orthopanel(_test_transformCoords)


def _test_transformCoords(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    mesh = fslvtk.VTKMesh(op.join(datadir, 'mesh_l_thal.vtk'))
    ref  = fslimage.Image(op.join(datadir, 'mesh_ref.nii.gz'))

    # resample to something other than 1mm^3
    # so display/voxel coord systems are different
    ref, xform = resample.resampleToPixdims(ref, [1.5, 1.5, 1.5])
    ref        = fslimage.Image(ref, xform=xform)

    overlayList.extend([ref, mesh])

    displayCtx.displaySpace = ref

    mopts = displayCtx.getOpts(mesh)
    ropts = displayCtx.getOpts(ref)

    mopts.refImage = ref

    # world display mesh
    spaces = ['world', 'display', 'mesh', 'voxel']

    (xlo, ylo, zlo), (xhi, yhi, zhi) = mesh.bounds

    coords = {
        'mesh'    : np.array([  xhi - xlo,  yhi - ylo,    zhi - zlo]),
        'world'   : np.array([ 3.92563438, 27.8010308,  34.60089011]),
        'display' : np.array([23.10099983, 32.8390007,  23.02000046]),
        'voxel'   : np.array([15.40066655, 21.89266713, 15.34666697]),
    }

    for from_, to in it.permutations(coords, 2):
        exp = coords[to]
        got = mopts.transformCoords(coords[from_],  from_, to)
        assert np.all(np.isclose(got, exp))
