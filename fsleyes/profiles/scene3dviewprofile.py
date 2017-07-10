#!/usr/bin/env python
#
# scene3dviewprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import logging

import wx

import numpy as np

import fsleyes.profiles as profiles


log = logging.getLogger(__name__)


class Scene3DViewProfile(profiles.Profile):

    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx):

        modes = ['rotate', 'zoom']

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes)

        self.__canvas = viewPanel.getGLCanvases()[0]


    def getEventTargets(self):
        return [self.__canvas]


    def _rotateModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        pass


    def _rotateModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        pass


    def _rotateModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        pass


    def _zoomModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        pass
