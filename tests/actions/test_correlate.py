#!/usr/bin/env python
#
# test_correlate.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np


from fsl.data.image import Image

import fsleyes.actions.correlate as correlate

from .. import realYield, run_with_orthopanel


def test_PearsonCorrelateAction():
    run_with_orthopanel(_test_PearsonCorrelateAction)

def _test_PearsonCorrelateAction(panel, overlayList, displayCtx):

    displayCtx = panel.displayCtx
    img3d = Image(np.random.randint(0, 1000, (10, 10, 10)))
    img4d = Image(np.random.randint(0, 1000, (10, 10, 10, 50)))
    overlayList.extend((img3d, img4d))
    realYield()
    opts = displayCtx.getOpts(img3d)
    displayCtx.location = opts.transformCoords((5, 5, 5), 'voxel', 'display')
    displayCtx.selectOverlay(img3d)
    realYield()
    assert not panel.pearsonCorrelation.enabled
    displayCtx.selectOverlay(img4d)
    realYield()
    assert panel.pearsonCorrelation.enabled
    panel.pearsonCorrelation()
    realYield(100)
    assert len(overlayList) == 3
    corr = overlayList[2]
    assert corr.shape == img4d.shape[:3]

    assert np.all(np.isclose(
        corr.data, correlate.pearsonCorrelation((5, 5, 5), img4d.data)))


def test_pearsonCorrelation():
    data   = np.random.randint(0, 1000, (10, 10, 10, 50))
    result = correlate.pearsonCorrelation((0, 0, 0), data)
    assert result.shape == data.shape[:3]
