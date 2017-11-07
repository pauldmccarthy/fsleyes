#!/usr/bin/env python
#
# scene3dviewprofile.py - The Scene3DViewProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Scene3DViewProfile` class, an interaction
:class:`.Profile` for :class:`.Scene3DPanel` views.
"""


import logging

import numpy as np

import fsleyes_props       as props
import fsl.utils.transform as transform
import fsl.utils.idle      as idle
import fsleyes.profiles    as profiles


log = logging.getLogger(__name__)


class Scene3DViewProfile(profiles.Profile):
    """The :class:`Scene3DViewProfile` class is a :class:`.Profile` for
    :class:`.Scene3DPanel` views. It defines mouse / keyboard handlers for
    interacting with the :class:`.Scene3DCanvas` contained in the panel.

    The following *modes* are defined (see the :class:`.Profile`
    documentation):

    ========== =================================================
    ``rotate`` Clicking and dragging the mouse rotates the scene
    ``zoom``   Moving the mouse wheel zooms in and out.
    ``pan``    Clicking and dragging the mouse pans the scene.
    ========== =================================================
    """

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
        """Returns a list containing the :class:`.Scene3DCanvas`.
        """
        return [self.__canvas]


    def resetDisplay(self):
        """Resets the :class:`.Scene3DCanvas` camera settings to their
        defaults.
        """

        opts = self.__canvas.opts

        with props.suppressAll(opts):
            opts.zoom     = 75
            opts.offset   = [0, 0]
            opts.rotation = np.eye(3)
        self.__canvas.Refresh()


    def _rotateModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse down events in ``rotate`` mode.
        Saves the mouse position and current rotation matrix (the
        :attr:`.Scene3DCanvas.rotation` property).
        """
        self.__rotateMousePos = mousePos
        self.__baseXform      = canvas.opts.rotation
        self.__lastRot        = np.eye(3)


    def _rotateModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse drag events in ``rotate`` mode.
        Modifies the canvas rotation matrix according to the X and Y
        mouse position (relative to the mouse down location).
        """

        if self.__rotateMousePos is None:
            return

        w, h   = canvas.GetSize()
        x0, y0 = self.__rotateMousePos
        x1, y1 = mousePos


        # Normalise x/y mouse pos to [-fac*pi, +fac*pi]
        fac = 1
        x0  = -1 + 2 * (x0 / float(w)) * fac * np.pi
        y0  = -1 + 2 * (y0 / float(h)) * fac * np.pi
        x1  = -1 + 2 * (x1 / float(w)) * fac * np.pi
        y1  = -1 + 2 * (y1 / float(h)) * fac * np.pi

        xrot = x1 - x0
        yrot = y1 - y0

        rot = transform.axisAnglesToRotMat(yrot, 0, xrot)

        self.__lastRot        = rot
        self.__rotateMousePos = mousePos

        canvas.opts.rotation = transform.concat(rot,
                                                self.__lastRot,
                                                self.__baseXform)


    def _rotateModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse up events in ``rotate`` mode.
        Clears the internal state used by the mouse down and drag
        handlers.
        """
        self.__rotateMousePos = None


    def _zoomModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Called on mouse wheel events in ``zoom`` mode. Adjusts the
        :attr:`.Scene3DCanvas.zoom` property.
        """

        if wheel == 0:
            return

        opts = canvas.opts

        def update():
            if   wheel > 0: opts.zoom += 0.1 * opts.zoom
            elif wheel < 0: opts.zoom -= 0.1 * opts.zoom

        # See comment in OrthoViewProfile._zoomModeMouseWheel
        # for the reason why we do this asynchronously.
        idle.idle(update, timeout=0.1)


    def _panModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse down events in ``pan`` mode. Saves the
        mouse position and current :attr:`.Scene3DCanvas.offset`
        value.
        """
        x, y = mousePos
        w, h = canvas.GetSize()
        x    = -1 + 2 * x / float(w)
        y    = -1 + 2 * y / float(h)

        self.__panMousePos    = (x, y)
        self.__panStartOffset = canvas.opts.offset[:]


    def _panModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse drag events in ``pan`` mode. Adjusts the
        :attr:`.Scene3DCanvas.offset` property.
        """
        if self.__panMousePos is None:
            return

        w,  h  = canvas.GetSize()
        sx, sy = self.__panMousePos
        ox, oy = self.__panStartOffset
        ex, ey = mousePos
        ex     = -1 + 2 * ex / float(w)
        ey     = -1 + 2 * ey / float(h)

        canvas.opts.offset = [ox + ex - sx, oy + ey - sy]


    def _panModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse up events in ``pan`` mode. Clears the
        internal state used by the down and drag handlers.
        """
        self.__panMousePos  = None
