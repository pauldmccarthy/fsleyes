#!/usr/bin/env python
#
# test_overlaytypes.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path           as op
import                      pytest
import fsl.utils.tempdir as tempdir
import fsl.utils.idle    as idle
import fsl.data.image    as fslimage
import fsl.data.dtifit   as fsldti
import fsl.data.vtk      as fslvtk
from . import              (run_with_orthopanel,
                            run_with_scene3dpanel,
                            compare_images,
                            realYield)


datadir = op.join(op.dirname(__file__), 'testdata')


def haveGL21():
    from fsl.utils.platform import platform as fslplatform
    return float(fslplatform.glVersion) >= 2.1


def _test_overlaytype(panel, overlayList, displayCtx, ovltype, overlay, **kwargs):

    import matplotlib.image           as mplimg
    import fsleyes.actions.screenshot as screenshot
    import fsleyes.views.orthopanel   as orthopanel

    if isinstance(panel, orthopanel.OrthoPanel):
        panel.sceneOpts.showCursor = False
        panel.sceneOpts.showLabels = False

    overlayList.append(overlay, overlayType=ovltype)

    opts = displayCtx.getOpts(overlay)
    for k, v in kwargs.items():
        setattr(opts, k, v)

    with tempdir.tempdir():

        fname = 'test_overlaytype_{}_{}.png'.format(
            ovltype, type(panel).__name__)

        realYield(100)
        idle.idle(screenshot.screenshot, panel, fname)
        realYield()

        bfname    = op.join(datadir, 'test_overlaytype_{}_{}.png'.format(
            ovltype, type(panel).__name__))
        screenshot = mplimg.imread(fname)
        benchmark  = mplimg.imread(bfname)

        result, diff = compare_images(screenshot, benchmark, 50)

        print('Comparing {} with {}: {}'.format(fname, bfname, diff))

        assert result

def test_volume():
    ovl = fslimage.Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_overlaytype, 'volume', ovl)

def test_mask():
    ovl = fslimage.Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_overlaytype, 'mask', ovl)

def test_label():
    ovl = fslimage.Image(op.join(datadir, '3d'))
    run_with_orthopanel(_test_overlaytype, 'label', ovl, lut='random')

def test_rgbvector():
    ovl = fsldti.DTIFitTensor(op.join(datadir, 'dti'))
    run_with_orthopanel(_test_overlaytype, 'rgbvector', ovl)

def test_linevector():
    ovl = fsldti.DTIFitTensor(op.join(datadir, 'dti'))
    run_with_orthopanel(_test_overlaytype, 'linevector', ovl)

@pytest.mark.skipif('not haveGL21()')
def test_tensor():
    ovl = fsldti.DTIFitTensor(op.join(datadir, 'dti'))
    run_with_orthopanel(_test_overlaytype, 'tensor', ovl)

@pytest.mark.skipif('not haveGL21()')
def test_sh():
    ovl = fslimage.Image(op.join(datadir, 'sh'))
    run_with_orthopanel(_test_overlaytype, 'sh', ovl)

def test_mesh():
    ovl = fslvtk.VTKMesh(op.join(datadir, 'mesh.vtk'), fixWinding=True)
    run_with_orthopanel(_test_overlaytype, 'mesh', ovl)

def test_volume_3d():
    ovl = fslimage.Image(op.join(datadir, '3d'))
    run_with_scene3dpanel(_test_overlaytype, 'volume', ovl)

def test_mesh_3d():
    ovl = fslvtk.VTKMesh(op.join(datadir, 'mesh.vtk'), fixWinding=True)
    run_with_scene3dpanel(_test_overlaytype, 'mesh', ovl)
