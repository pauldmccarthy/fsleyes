#!/usr/bin/env python
#
# orthoviewprofile.py - The OrthoViewProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoViewProfile` class, an interaction
:class:`.Profile` for :class:`.OrthoPanel` views.
"""

import logging

import wx

import fsl.fsleyes.profiles as profiles


log = logging.getLogger(__name__)


class OrthoViewProfile(profiles.Profile):
    """The ``OrthoViewProfile`` class is a :class:`.Profile` for the
    :class:`.OrthoPanel` class.  It defines mouse/keyboard handlers which
    allow the user to navigate through the ``OrthoPanel`` display of the
    overlays in the :class:`.OverlayList`.
    
    ``OrthoViewProfile`` defines three *modes* (see the :class:`.Profile`
    class documentation):

    ======== ==============================================================
    ``nav``  The user can change the currently displayed location. This is
             accomplished by updating the :attr:`.DisplayContext.location`
             property on left mouse drags.
    
    ``zoom`` The user can zoom in/out of a canvas with the mouse wheel, and
             draw a rectangle on a canvas in which to zoom. This is
             accomplished by updating the :attr:`.SliceCanvasOpts.zoom`
             property on mouse wheel changes, and displaying a
             :class:`~.annotations.Rect` annotation on left mouse drags.
    
    ``pan``  The user can pan around a canvas (if the canvas is zoomed in).
             This is accomplished by calling the
             :meth:`.SliceCanvas.panDisplayBy` on left mouse drags.
    ======== ==============================================================


    The ``OrthoViewProfile`` class also defines a few actions:


    ================ ========================================================
    ``resetZoom``    Resets the zoom on every :class:`.SliceCanvas` to 100%.
    ``centreCursor`` Moves the :attr:`.DisplayContext.location` to the centre
                     of the display coordinate system.
    ================ ========================================================
    """

    
    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx,
                 extraModes=None,
                 extraActions=None):
        """Creates an :class:`OrthoViewProfile`, which can be registered
        with the given ``viewPanel``.


        .. note:: The :class:`.OrthoEditProfile` is a sub-class of the 
                  ``OrthoViewProfile``. It uses the ``extraModes`` and
                  ``extraActions`` arguments to set up its edit-related
                  modes/actions.

        :arg viewPanel:    An :class:`.OrthoPanel` instance.
        
        :arg overlayList:  The :class:`.OverlayList` instance.
        
        :arg displayCtx:   The :class:`.DisplayContext` instance.
        
        :arg extraModes:   Extra modes to pass through to the
                           :class:`.Profile` constructor.
        
        :arg extraActions: Extra actions to pass through to the
                           :class:`.Profile` constructor.
        """

        if extraModes   is None: extraModes   = []
        if extraActions is None: extraActions = {}

        modes   = ['nav', 'pan', 'zoom']
        actionz = {
            'resetZoom'    : self.resetZoom,
            'centreCursor' : self.centreCursor,
        }

        modes   = modes + extraModes
        actionz = dict(actionz.items() + extraActions.items())

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes,
                                  actionz)

        self.__xcanvas = viewPanel.getXCanvas()
        self.__ycanvas = viewPanel.getYCanvas()
        self.__zcanvas = viewPanel.getZCanvas()

        # This attribute will occasionally store a
        # reference to a gl.annotations.Rect -
        # see the _zoomModeLeftMouse* handlers
        self.__lastRect = None


    def getEventTargets(self):
        """Overrides :meth:`.Profile.getEventTargets`.

        Returns the three :class:`.SliceCanvas` instances displayed in the
        :class:`.OrthoPanel` instance that is using this ``OrthoViewProfile``.
        """
        return [self.__xcanvas, self.__ycanvas, self.__zcanvas]


    def resetZoom(self, *a):
        """Sets the :class:`.SceneOpts.zoom`, :class:`.OrthoOpts.xzoom`,
        :class:`.OrthoOpts.yzoom`,  and :class:`.OrthoOpts.zzoom` properties
        to 100%.
        """

        opts = self._viewPanel.getSceneOptions()

        opts.zoom  = 100
        opts.xzoom = 100
        opts.yzoom = 100
        opts.zzoom = 100


    def centreCursor(self, *a):
        """Sets the :attr:`.DisplayContext.location` to the centre of the
        :attr:`.DisplayContext.bounds`.
        """

        bounds = self._displayCtx.bounds

        xmid = bounds.xlo + 0.5 * bounds.xlen
        ymid = bounds.ylo + 0.5 * bounds.ylen
        zmid = bounds.zlo + 0.5 * bounds.zlen

        self._displayCtx.location.xyz = [xmid, ymid, zmid]


    ########################
    # Navigate mode handlers
    ########################

    
    def __getNavOffsets(self):
        """Used by some ``nav`` mode handlers. Returns a sequence of three
        values, one per display space axis, which specify the distance that
        a navigation operation should move the display.

        If the currently selected overlay is an :class:`.Image` instance, the
        distance that a navigation operation should shift the display will
        differ depending on the value of the :attr:`.ImageOpts.transform`
        property. For example, if ``transform`` is ``id``, the display should
        be moved by one unit (which corresponds to one voxel). But if the
        ``transform`` is ``pixdim``, the display should be moved by one pixdim
        (e.g. 2, for a "math:`2mm^3` image).
        """
        
        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        # The currently selected overlay is non-volumetric,
        # and does not have a reference image
        if overlay is None:
            offsets = [1, 1, 1]

        # We have a voluemtric reference image to play with
        else:

            opts = self._displayCtx.getOpts(overlay)

            # If we're displaying voxel space,
            # we want a keypress to move one
            # voxel in the appropriate direction
            if   opts.transform == 'id':     offsets = [1, 1, 1]
            elif opts.transform == 'pixdim': offsets = overlay.pixdim

            # Otherwise we'll just move an arbitrary 
            # amount in the image world space - 1mm
            else:                            offsets = [1, 1, 1]

        return offsets


    def _navModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles left mouse drags in ``nav`` mode.
        
        Left mouse drags in ``nav`` mode update the
        :attr:`.DisplayContext.location` to follow the mouse location.
        """

        if canvasPos is None:
            return

        self._displayCtx.location = canvasPos

        
    def _navModeChar(self, ev, canvas, key):
        """Handles key presses in ``nav`` mode.

        Arrow key presses in ``nav`` mode update the
        :attr:`.DisplayContext.location`.  Arrow keys map to the
        horizontal/vertical axes, and -/+ keys map to the depth axis of the
        canvas which was the target of the event.

        Page up/page down changes the :attr:`.DisplayContext.selectedOverlay`.
        """

        if len(self._overlayList) == 0:
            return

        pos     = self._displayCtx.location.xyz
        offsets = self.__getNavOffsets()

        try:    ch = chr(key)
        except: ch = None

        if   key == wx.WXK_LEFT:  pos[canvas.xax] -= offsets[canvas.xax]
        elif key == wx.WXK_RIGHT: pos[canvas.xax] += offsets[canvas.xax]
        elif key == wx.WXK_UP:    pos[canvas.yax] += offsets[canvas.yax]
        elif key == wx.WXK_DOWN:  pos[canvas.yax] -= offsets[canvas.yax]
        elif ch  in ('-', '_'):   pos[canvas.zax] -= offsets[canvas.zax]
        elif ch  in ('+', '='):   pos[canvas.zax] += offsets[canvas.zax]

        elif key in (wx.WXK_PAGEUP, wx.WXK_PAGEDOWN):
            overlay = self._displayCtx.getSelectedOverlay()
            idx     = self._displayCtx.getOverlayOrder(overlay)

            if   key == wx.WXK_PAGEUP:   idx += 1
            elif key == wx.WXK_PAGEDOWN: idx -= 1

            idx    %= len(self._overlayList)
            idx     = self._displayCtx.overlayOrder[idx]

            self._displayCtx.selectedOverlay = idx 

        self._displayCtx.location.xyz = pos


    def _navModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Handles mouse wheel movement in ``nav`` mode.

        Mouse wheel movement on a canvas changes the depth location displayed
        on that canvas.
        """

        if len(self._overlayList) == 0:
            return

        pos     = self._displayCtx.location.xyz
        offsets = self.__getNavOffsets()

        if   wheel > 0: pos[canvas.zax] -= offsets[canvas.zax]
        elif wheel < 0: pos[canvas.zax] += offsets[canvas.zax]

        self._displayCtx.location.xyz = pos        

        
    ####################
    # Zoom mode handlers
    ####################

        
    def _zoomModeMouseWheel(self,
                            ev, 
                            canvas,
                            wheel,
                            mousePos=None,
                            canvasPos=None):
        """Handles mouse wheel events in ``zoom`` mode.

        Mouse wheel motion in zoom mode increases/decreases the zoom level
        of the target canvas.
        """
        if   wheel > 0: wheel =  50
        elif wheel < 0: wheel = -50
        canvas.zoom += wheel

        
    def _zoomModeChar(self, ev, canvas, key):
        """Handles key presses in ``zoom`` mode.

        The +/- keys in zoom mode increase/decrease the zoom level
        of the target canvas.
        """

        try:    ch = chr(key)
        except: ch = None

        zoom = 0

        if   key == wx.WXK_DOWN: zoom = -1
        elif key == wx.WXK_UP:   zoom =  1
        elif ch  == '-':         zoom = -1
        elif ch  in ('=', '+'):  zoom =  1

        if zoom == 0:
            return

        self._zoomModeMouseWheel(canvas, zoom)

        
    def _zoomModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles left mouse drags in ``zoom`` mode.

        Left mouse drags in zoom mode draw a rectangle on the target
        canvas.

        When the user releases the mouse (see :meth:`_zoomModeLeftMouseUp`),
        the canvas will be zoomed in to the drawn rectangle.
        """

        if canvasPos is None:
            return

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        corner = [canvasDownPos[canvas.xax], canvasDownPos[canvas.yax]]
        width  = canvasPos[canvas.xax] - corner[0]
        height = canvasPos[canvas.yax] - corner[1]

        self.__lastRect = canvas.getAnnotations().rect(corner,
                                                       width,
                                                       height,
                                                       colour=(1, 1, 0))
        canvas.Refresh()

        
    def _zoomModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles left mouse up events in ``zoom`` mode.

        When the left mouse is released in zoom mode, the target
        canvas is zoomed in to the rectangle region that was drawn by the
        user.
        """

        if canvasPos is None:
            return

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        if self.__lastRect is not None:
            canvas.getAnnotations().dequeue(self.__lastRect)
            self.__lastRect = None

        rectXlen = abs(canvasPos[canvas.xax] - canvasDownPos[canvas.xax])
        rectYlen = abs(canvasPos[canvas.yax] - canvasDownPos[canvas.yax])

        if rectXlen == 0: return
        if rectYlen == 0: return

        rectXmid = (canvasPos[canvas.xax] + canvasDownPos[canvas.xax]) / 2.0
        rectYmid = (canvasPos[canvas.yax] + canvasDownPos[canvas.yax]) / 2.0

        xlen = self._displayCtx.bounds.getLen(canvas.xax)
        ylen = self._displayCtx.bounds.getLen(canvas.yax)

        xzoom   = xlen / rectXlen
        yzoom   = ylen / rectYlen
        zoom    = min(xzoom, yzoom) * 100.0
        maxzoom = canvas.getConstraint('zoom', 'maxval')

        if zoom >= maxzoom:
            zoom = maxzoom

        if zoom > canvas.zoom:
            canvas.zoom = zoom
            canvas.centreDisplayAt(rectXmid, rectYmid)

        canvas.Refresh()
        
        
    ###################
    # Pan mode handlers
    ###################
    
        
    def _panModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles left mouse drags in ``pan`` mode.

        Left mouse drags in pan mode move the target canvas display about
        to follow the mouse.

        If the target canvas is not zoomed in, this has no effect.
        """

        if canvasPos is None:
            return
        
        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        xoff = canvasPos[canvas.xax] - canvasDownPos[canvas.xax]
        yoff = canvasPos[canvas.yax] - canvasDownPos[canvas.yax]

        canvas.panDisplayBy(-xoff, -yoff)

    
    def _panModeChar(self, ev, canvas, key):
        """Handles key presses in ``pan`` mode.

        The arrow keys in pan mode move the target canvas display around
        (unless the canvas is not zoomed in).
        """

        xoff = 0
        yoff = 0
        
        if   key == wx.WXK_DOWN:  yoff = -2
        elif key == wx.WXK_UP:    yoff =  2
        elif key == wx.WXK_LEFT:  xoff = -2
        elif key == wx.WXK_RIGHT: xoff =  2
        else:                     return

        canvas.panDisplayBy(xoff, yoff)
