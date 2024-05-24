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

import          wx
import numpy as np

import fsleyes_props      as props
from   fsl.transform import affine
from   fsl.utils     import idle
from   fsleyes       import profiles
from   fsleyes       import actions
from   fsleyes.utils import lazyimport


log = logging.getLogger(__name__)


gl = lazyimport('OpenGL.GL', f'{__name__}.gl')


class Scene3DViewProfile(profiles.Profile):
    """The :class:`Scene3DViewProfile` class is a :class:`.Profile` for
    :class:`.Scene3DPanel` views. It defines mouse / keyboard handlers for
    interacting with the :class:`.Scene3DCanvas` contained in the panel.

    The following *modes* are defined (see the :class:`.Profile`
    documentation):

    ========== ========================================================
    ``rotate`` Clicking and dragging the mouse rotates the scene
    ``zoom``   Moving the mouse wheel zooms in and out.
    ``pan``    Clicking and dragging the mouse pans the scene.
    ``pick``   Clicking changes the :attr:`.DisplayContext.location`
    ========== ========================================================
    """


    @staticmethod
    def supportedView():
        """Specifies that this profile can only work with the
        :class:`.Scene3DPanel` view.
        """
        from fsleyes.views.scene3dpanel import Scene3DPanel
        return Scene3DPanel


    @staticmethod
    def tempModes():
        """Returns the temporary mode map for the ``Scene3DViewProfile``,
        which controls the use of modifier keys to temporarily enter other
        interaction modes.
        """
        return {
            ('rotate', wx.WXK_CONTROL) : 'zoom',
            ('rotate', wx.WXK_ALT)     : 'pan',
            ('rotate', wx.WXK_SHIFT)   : 'pick'}


    @staticmethod
    def altHandlers():
        """Returns the alternate handlers map, which allows event handlers
        defined in one mode to be re-used whilst in another mode.
        """
        return {
            ('rotate', 'MiddleMouseDown') : ('pan', 'LeftMouseDown'),
            ('rotate', 'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),
            ('rotate', 'MiddleMouseUp')   : ('pan', 'LeftMouseUp')}


    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx):

        modes = ['rotate', 'zoom', 'pan', 'pick']

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


    @actions.action
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

        rot = affine.axisAnglesToRotMat(yrot, 0, xrot)

        self.__lastRot        = rot
        self.__rotateMousePos = mousePos

        canvas.opts.rotation = affine.concat(rot,
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


    def _pickModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse down events in ``pick`` mode.

        Updates the :attr:`DisplayContext.location` property.
        """

        from fsl.data.mesh  import Mesh
        from fsl.data.image import Image

        displayCtx  = self.displayCtx
        overlayList = self.overlayList
        ovl         = displayCtx.getSelectedOverlay()

        if ovl is None:
            return

        opts = self.displayCtx.getOpts(ovl)

        # The canvasPos is located on the near clipping
        # plane (see Scene3DCanvas.canvasToWorld).
        # We also need the corresponding point on the
        # far clipping plane.
        farPos = canvas.canvasToWorld(mousePos[0], mousePos[1], near=False)

        # For image overlays, we transform screen
        # coordinates into display coordinates, via
        # a texture to screen coord affine, which
        # is cached by the glvolume draw functions.
        if isinstance(ovl, Image):

            screen2Display = overlayList.getData(
                ovl, 'screen2DisplayXform_{}'.format(id(opts)), None)

            if screen2Display is None:
                return

            # Retrieve the depth for the current
            # fragment. Images are drawn to an off-screen
            # texture (see GLVolume.draw3d), so we can get
            # the depth from there.
            globj = canvas.getGLObject(ovl)
            tex = globj.renderTexture1.depthTexture
            with tex.bound():
                # There's no function to read part of
                # a texture in GL < 4.5, so we have
                # to read the entire depth testure.
                buf = gl.glGetTexImage(gl.GL_TEXTURE_2D,
                                       0,
                                       tex.baseFormat,
                                       tex.textureType,
                                       None)

            # Get the mouse coords, convert them into
            # texture indices (the texture may not have
            # the same size as the canvas) and transform
            # them into normalised device coordinates
            # (NDCs, in the range [0, 1] - see
            # Volume3DOpts.calculateRayCastSettings),
            x, y   = mousePos
            w, h   = canvas.GetSize()
            tw, th = tex.shape
            x      = x / w
            y      = y / h
            tx     = int(round(x * tw))
            ty     = int(round(y * th))

            # The depth texure data is stored as uint32,
            # but represents floating point values in
            # the range [0, 1]. Also, the texture buffer
            # axis ordering seems to be flipped.
            buf = buf.reshape(th, tw)
            z   = buf[ty, tx] / 4294967295.0

            # Transform NDCs into display coordinates
            xyz = affine.transform([x, y, z], screen2Display)
            self.displayCtx.location.xyz = xyz

        else:
            opts      = self.displayCtx.getOpts(ovl)
            rayOrigin = canvasPos
            rayDir    = affine.normalise(farPos - canvasPos)

            # transform location from display into model space
            rayOrigin = opts.transformCoords(rayOrigin, 'display', 'mesh')
            rayDir    = opts.transformCoords(rayDir,    'display', 'mesh',
                                             vector=True)
            loc, tri  = ovl.rayIntersection([rayOrigin],
                                            [rayDir],
                                            vertices=True)

            if len(loc) == 0:
                return

            loc = loc[0]
            tri = ovl.indices[int(tri[0]), :]

            # The rayIntersection method gives us a
            # point on one of the mesh triangles -
            # we want the vertex on that triangle
            # which is nearest to the intersection.
            triVerts = ovl.vertices[tri, :]
            triDists = affine.veclength(loc - triVerts)
            vertIdx  = np.argsort(triDists)[0]

            loc      = ovl.vertices[tri[vertIdx], :]
            loc      = opts.transformCoords(loc, 'mesh', 'display')

            self.displayCtx.location.xyz = loc


    def _pickModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse drag events in ``pick`` mode. Forwards the
        event to the :meth:`_pickModeLeftMouseDown` method.
        """
        self._pickModeLeftMouseDown(ev, canvas, mousePos, canvasPos)
