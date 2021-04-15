#!/usr/bin/env python
#
# test_atlaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsleyes.plugins.controls.atlaspanel as ap

from fsleyes.tests import run_with_orthopanel, yieldUntil, realYield


def test_atlaspanel_toggleOverlay():
    run_with_orthopanel(_test_atlaspanel_toggleOverlay)

def _test_atlaspanel_toggleOverlay(panel, overlayList, displayCtx):

    loaded = [False]
    def onload():
        loaded[0] = True
    def hasloaded():
        return loaded[0]

    panel.togglePanel(ap.AtlasPanel)
    atlaspanel = panel.getPanel(ap.AtlasPanel)

    atlaspanel.toggleOverlay('harvardoxford-cortical',
                             None, summary=True, onLoad=onload)
    yieldUntil(hasloaded)
    assert len(overlayList) == 1
    img = overlayList[0]
    assert img.ndim == 3

    atlaspanel = None
    overlayList.clear()
    realYield()
    panel.togglePanel(ap.AtlasPanel)
    realYield()
