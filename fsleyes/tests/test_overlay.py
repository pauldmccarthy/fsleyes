#!/usr/bin/env python


import os.path as op
import            os
import            shutil

from fsl.utils.tempdir   import tempdir
from fsl.data.image      import Image
from fsl.data.vtk        import VTKMesh
from fsl.data.freesurfer import FreesurferMesh
from fsl.data.gifti      import GiftiMesh

from fsleyes.tests import run_with_fsleyes, realYield, testdir, random_image

import fsleyes.overlay as fslovl


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


def test_findFEATImage():
    contents = ['analysis.feat/design.con',
                'analysis.feat/design.fsf',
                'analysis.feat/design.mat']

    funcfile   = 'analysis.feat/filtered_func_data.nii.gz'
    exfuncfile = 'analysis.feat/example_func.nii.gz'

    overlayList = fslovl.OverlayList()

    with testdir(contents) as featdir:
        random_image(funcfile,   (20, 20, 20, 20))
        random_image(exfuncfile, (20, 20, 20))

        exfunc = Image(exfuncfile)
        func   = Image(funcfile)

        overlayList.append(exfunc)
        assert fslovl.findFEATImage(overlayList, exfunc) is None
        overlayList.append(func)
        assert fslovl.findFEATImage(overlayList, exfunc) is func



def test_findVTKReferenceImage():
    vtkfile = op.join(datadir, 'mesh_l_thal.vtk')
    reffile = op.join(datadir, 'mesh_ref.nii.gz')

    with tempdir():
        vtkfile = shutil.copy(vtkfile, 'struc-L_Thal_first.vtk')
        reffile = shutil.copy(reffile, 'struc.nii.gz')
        mesh    = VTKMesh(vtkfile)
        ref     = Image(reffile)
        overlayList = fslovl.OverlayList([mesh])
        assert fslovl.findMeshReferenceImage(overlayList, mesh) is None
        overlayList.append(ref)
        assert fslovl.findMeshReferenceImage(overlayList, mesh) is ref


def test_findFreeSurferReferenceImage():
    surffile = op.join(datadir, 'freesurfer', 'lh.pial')
    reffile  = op.join(datadir, '3d.nii.gz')

    with tempdir():
        os.mkdir('mri')
        os.mkdir('surf')
        surffile = shutil.copy(surffile, op.join('surf', 'lh.pial'))
        reffile  = shutil.copy(reffile,  op.join('mri', 'orig.nii.gz'))
        surf     = FreesurferMesh(surffile)
        ref      = Image(reffile)

        overlayList = fslovl.OverlayList([surf])
        assert fslovl.findMeshReferenceImage(overlayList, surf) is None
        overlayList.append(ref)
        assert fslovl.findMeshReferenceImage(overlayList, surf) is ref


def test_findAnyReferenceImage():
    surffile = op.join(datadir, 'gifti', 'white.surf.gii')
    reffile  = op.join(datadir, '3d.nii.gz')

    with tempdir():
        surffile = shutil.copy(surffile, op.join('white.surf.gii'))
        reffile  = shutil.copy(reffile,  op.join('mri.nii.gz'))
        surf     = GiftiMesh(surffile)
        ref      = Image(reffile)

        overlayList = fslovl.OverlayList([surf])
        assert fslovl.findMeshReferenceImage(overlayList, surf) is None
        overlayList.append(ref)
        assert fslovl.findMeshReferenceImage(overlayList, surf) is ref
