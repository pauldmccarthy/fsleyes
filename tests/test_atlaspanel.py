#!/usr/bin/env python
#
# test_atlaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsleyes.controls.atlaspanel as ap

from . import run_with_orthopanel, yieldUntil, realYield


def test_atlaspanel_toggleOverlay():
    run_with_orthopanel(_test_atlaspanel_toggleOverlay)

def _test_atlaspanel_toggleOverlay(panel, overlayList, displayCtx):

    loaded = [False]
    def onload():
        loaded[0] = True
    def hasloaded():
        return loaded[0]

    panel.toggleAtlasPanel()
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
    panel.toggleAtlasPanel()
    realYield()
