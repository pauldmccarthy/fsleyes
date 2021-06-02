#!/usr/bin/env python
#
# test_plotlistpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

from fsl.data.image import Image

from fsleyes.views.timeseriespanel import TimeSeriesPanel
from fsleyes.controls.plotlistpanel import PlotListPanel

from fsleyes.tests import run_with_timeseriespanel, realYield


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_PlotListPanel():
    run_with_timeseriespanel(_test_PlotListPanel)

def _test_PlotListPanel(panel : TimeSeriesPanel, overlayList, displayCtx):

    img = Image(op.join(datadir, '4d'))
    overlayList.append(img)
    realYield()

    pcanvas    = panel.canvas
    displayCtx = panel.displayCtx
    opts       = displayCtx.getOpts(img)

    if not panel.isPanelOpen(PlotListPanel):
        panel.togglePanel(PlotListPanel)
    plist = panel.getPanel(PlotListPanel)
    realYield()

    class MockEvent:
        def __init__(self, ds, label=None):
            self.data  = ds
            self.label = label

    displayCtx.location = opts.transformCoords([5, 5, 2], 'voxel', 'display')
    realYield()
    assert len(pcanvas.dataSeries) == 0

    plist.onListAdd(None)
    realYield()
    assert len(pcanvas.dataSeries) == 1

    ds1 = pcanvas.dataSeries[0]

    displayCtx.location = opts.transformCoords([5, 5, 3], 'voxel', 'display')
    realYield()
    plist.onListAdd(None)
    realYield()
    assert len(pcanvas.dataSeries) == 2
    ds2 = pcanvas.dataSeries[1]

    plist.onListSelect(MockEvent(ds1))
    realYield()
    assert np.all(np.isclose(opts.getVoxel(), [5, 5, 2]))

    plist.onListSelect(MockEvent(ds2))
    realYield()
    assert np.all(np.isclose(opts.getVoxel(), [5, 5, 3]))

    plist.onListEdit(MockEvent(ds1, 'newlabel'))
    assert ds1.label == 'newlabel'

    plist.onListRemove(MockEvent(ds2))
    realYield()
    assert list(pcanvas.dataSeries) == [ds1]

    plist.onListRemove(MockEvent(ds1))
    realYield()
    assert len(pcanvas.dataSeries) == 0
