#!/usr/bin/env python
#
# scene3dviewprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import logging

import wx

import numpy as np

import fsl.utils.transform   as transform
import fsleyes.profiles      as profiles


log = logging.getLogger(__name__)


class Scene3DViewProfile(profiles.Profile):

    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx):

        modes = ['rotate', 'zoom', 'pan']

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes)

        self.__canvas         = viewPanel.getGLCanvases()[0]
        self.__rotateMousePos = None
        self.__panMousePos    = None
        self.__panCanvasPos   = None


    def getEventTargets(self):
        return [self.__canvas]


    def _rotateModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        self.__rotateMousePos = mousePos
        self.__baseXform      = canvas.rotation
        self.__lastRot        = np.eye(3)


    def _rotateModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        if self.__rotateMousePos is None:
            return

        w, h = canvas._getSize()

        x0, y0 = self.__rotateMousePos
        x1, y1 = mousePos


        # Normalise x/y mouse pos to [-fac*pi, +fac*pi]
        fac = 1

        x0 = -1 + 2 * (x0 / float(w)) * fac * np.pi
        y0 = -1 + 2 * (y0 / float(h)) * fac * np.pi
        x1 = -1 + 2 * (x1 / float(w)) * fac * np.pi
        y1 = -1 + 2 * (y1 / float(h)) * fac * np.pi

        xrot = x1 - x0
        yrot = y0 - y1

        rot   = transform.axisAnglesToRotMat(yrot, 0, xrot)
        rot   = transform.invert(rot)

        self.__lastRot        = rot
        self.__rotateMousePos = mousePos

        canvas.rotation = transform.concat(rot,
                                           self.__lastRot,
                                           self.__baseXform)


    def _rotateModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self.__rotateMousePos = None


    def _zoomModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):

        if wheel == 0:
            return

        if   wheel > 0: canvas.zoom += 0.1 * canvas.zoom
        elif wheel < 0: canvas.zoom -= 0.1 * canvas.zoom


    def _panModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        self.__panMousePos  = mousePos
        self.__panCanvasPos = canvasPos


    def _panModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        if self.__panMousePos is None:
            return



    def _panModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self.__panMousePos  = None
        self.__panCanvasPos = None
