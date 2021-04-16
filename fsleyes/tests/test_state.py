#!/usr/bin/env python
#
# test_state.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

from fsl.data.image import Image
from fsl.data.vtk   import VTKMesh

import fsleyes.state as state
from fsleyes.views.orthopanel import OrthoPanel
from fsleyes.views.histogrampanel import HistogramPanel

from fsleyes.tests import run_with_fsleyes, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_state(frame, overlayList, displayCtx):

    rfile = op.join(datadir, 'mesh_ref.nii.gz')
    mfile = op.join(datadir, 'mesh_l_thal.vtk')

    overlayList.append(Image(  rfile))
    overlayList.append(VTKMesh(mfile))

    ref, mesh = overlayList
    ropts     = displayCtx.getOpts(ref)
    mopts     = displayCtx.getOpts(mesh)

    ropts.cmap     = 'hot'
    mopts.refImage = ref
    mopts.outline  = True

    frame.addViewPanel(OrthoPanel)
    frame.addViewPanel(HistogramPanel)

    oopts = frame.viewPanels[0].sceneOpts
    oopts.showXCanvas = False
    oopts.zzoom       = 2000
    frame.viewPanels[1].canvas.smooth = True
    frame.viewPanels[1].histType      = 'count'

    realYield(200)
    st = state.getState(frame)

    frame.removeAllViewPanels()
    del overlayList[:]

    realYield(200)
    state.setState(frame, st)
    realYield(200)

    ortho, hist = frame.viewPanels
    assert isinstance(ortho, OrthoPanel)
    assert isinstance(hist,  HistogramPanel)

    assert not ortho.sceneOpts.showXCanvas
    assert     ortho.sceneOpts.zzoom == 2000
    assert     hist.canvas.smooth
    assert     hist.histType == 'count'

    ref, mesh = overlayList

    assert isinstance(ref,  Image)
    assert isinstance(mesh, VTKMesh)

    ropts = displayCtx.getOpts(ref)
    mopts = displayCtx.getOpts(mesh)

    assert ropts.cmap.name == 'hot'
    assert mopts.refImage is ref
    assert mopts.outline


def test_state():
    run_with_fsleyes(_test_state)
