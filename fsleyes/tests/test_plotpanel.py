#!/usr/bin/env python
#
# test_plotpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

from fsl.data.image import Image
from fsleyes.tests import run_with_timeseriespanel, realYield

datadir = op.join(op.dirname(__file__), 'testdata')

# regression test - the overlayplotpanel would
# de-register listeners if a single image
# was removed
def test_two_overlays_one_removed():
    run_with_timeseriespanel(_test_two_overlays_one_removed)

def _test_two_overlays_one_removed(panel, overlayList, displayCtx):
    displayCtx = panel.displayCtx
    img1 = Image(op.join(datadir, '4d'))
    img2 = Image(img1.data * 20, xform=img1.voxToWorldMat)
    overlayList.extend((img1, img2))
    realYield()
    opts2 = displayCtx.getOpts(img2)
    x, y, z = img1.shape[0] // 2, img1.shape[1] // 2, img1.shape[2] // 2
    loc     = opts2.transformCoords((x, y, z), 'voxel', 'display')
    displayCtx.location = loc
    realYield()

    ts1 = panel.getDataSeries(img1)
    ts2 = panel.getDataSeries(img2)

    assert np.all(ts1.getData()[1] == img1[x, y, z, :])
    assert np.all(ts2.getData()[1] == img2[x, y, z, :])

    x += 1
    y -= 1
    z -= 1
    loc = opts2.transformCoords((x, y, z), 'voxel', 'display')
    displayCtx.location = loc
    realYield()
    assert np.all(ts1.getData()[1] == img1[x, y, z, :])
    assert np.all(ts2.getData()[1] == img2[x, y, z, :])

    overlayList.remove(img1)
    realYield()
    x -= 2
    y += 2
    z -= 1
    loc = opts2.transformCoords((x, y, z), 'voxel', 'display')
    displayCtx.location = loc
    realYield()
    assert np.all(ts2.getData()[1] == img2[x, y, z, :])
