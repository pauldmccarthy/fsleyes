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

        modes = ['rotate', 'zoom']

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes)

        self.__canvas    = viewPanel.getGLCanvases()[0]
        self.__mousePos  = None


    def getEventTargets(self):
        return [self.__canvas]


    def _rotateModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        self.__mousePos  = mousePos
        self.__baseXform = canvas.xform
        self.__lastRot   = np.eye(3)


    def _rotateModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        if self.__mousePos is None:
            return

        w, h = canvas._getSize()

        x0, y0 = self.__mousePos
        x1, y1 = mousePos

        fac = 1

        # Convert pixels to [-4pi, 4pi]
        x0 = -1 + 2 * (x0 / float(w)) * fac * np.pi
        y0 = -1 + 2 * (y0 / float(h)) * fac * np.pi
        x1 = -1 + 2 * (x1 / float(w)) * fac * np.pi
        y1 = -1 + 2 * (y1 / float(h)) * fac * np.pi

        xrot = x0 - x1
        yrot = y1 - y0

        rot   = transform.axisAnglesToRotMat(yrot, 0, xrot)
        rot   = transform.invert(rot)
        rot   = transform.concat(rot, self.__lastRot)

        xform = transform.compose([1, 1, 1], [0, 0, 0], rot, canvas.centre)
        xform = transform.concat(xform, self.__baseXform)

        canvas.xform = xform

        self.__lastRot  = rot
        self.__mousePos = mousePos

        canvas.Refresh()


    def _rotateModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self.__mousePos = None


    def _zoomModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):

        if wheel == 0:
            return

        if   wheel > 0: canvas.zoom -= 0.1 * canvas.zoom
        elif wheel < 0: canvas.zoom += 0.1 * canvas.zoom
