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

import numpy as np

import fsl.fsleyes.profiles as profiles
import fsl.fsleyes.actions  as actions
import fsl.utils.async      as async
import fsl.data.image       as fslimage
import fsl.data.constants   as constants


log = logging.getLogger(__name__)


class OrthoViewProfile(profiles.Profile):
    """The ``OrthoViewProfile`` class is a :class:`.Profile` for the
    :class:`.OrthoPanel` class.  It defines mouse/keyboard handlers which
    allow the user to navigate through the ``OrthoPanel`` display of the
    overlays in the :class:`.OverlayList`.
    
    ``OrthoViewProfile`` defines the following *modes* (see the
    :class:`.Profile` class documentation):

    ========== ==============================================================
    ``nav``    The user can change the currently displayed location. This is
               accomplished by updating the :attr:`.DisplayContext.location`
               property on left mouse drags.

    ``slice``  The user can change the current slice shown on a single
               canvas.
    
    ``zoom``   The user can zoom in/out of a canvas with the mouse wheel, and
               draw a rectangle on a canvas in which to zoom. This is
               accomplished by updating the :attr:`.SliceCanvasOpts.zoom`
               property on mouse wheel changes, and displaying a
               :class:`~.annotations.Rect` annotation on left mouse drags.
    
    ``pan``    The user can pan around a canvas (if the canvas is zoomed in).
               This is accomplished by calling the
               :meth:`.SliceCanvas.panDisplayBy` on left mouse drags.

    ``bricon`` The user can drag the mouse along a canvas to change the
               brightness/contrast of the currently selected overlay.
    ========== ==============================================================


    The ``OrthoViewProfile`` class also defines a few :mod:`.actions`:

    .. autosummary::
       :nosignatures:

       resetZoom
       centreCursor
    """

    
    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx,
                 extraModes=None):
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
        """

        if extraModes is None:
            extraModes = []

        modes = ['nav', 'slice', 'pan', 'zoom', 'bricon'] + extraModes

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes)

        # We create our own name and use it
        # for registering property listeners,
        # so sub-classes can use Profile._name
        # to register its own listeners.
        self.__name    = 'OrthoViewProfile_{}'.format(self._name)

        self.__xcanvas = viewPanel.getXCanvas()
        self.__ycanvas = viewPanel.getYCanvas()
        self.__zcanvas = viewPanel.getZCanvas()

        # This attribute will occasionally store a
        # reference to a gl.annotations.Rect -
        # see the _zoomModeLeftMouse* handlers
        self.__lastRect = None

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged) 
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)


    def destroy(self):
        """Must be called when this ``OrthoViewProfile`` is no longer needed.
        Removes some property listeners, and calls :meth:`.Profile.destroy`.
        """
        self._overlayList.removeListener('overlays',        self.__name)
        self._displayCtx .removeListener('selectedOverlay', self.__name)
        profiles.Profile.destroy(self)


    def getEventTargets(self):
        """Overrides :meth:`.Profile.getEventTargets`.

        Returns the three :class:`.SliceCanvas` instances displayed in the
        :class:`.OrthoPanel` instance that is using this ``OrthoViewProfile``.
        """
        return [self.__xcanvas, self.__ycanvas, self.__zcanvas]


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes. Enables/disables
        the action methods based on the newly selected overlay.
        """
        
        ovl = self._displayCtx.getSelectedOverlay()
        
        if   ovl is None:                                       enable = False
        elif not isinstance(ovl, fslimage.Nifti1):              enable = False
        elif ovl.getXFormCode != constants.NIFTI_XFORM_MNI_152: enable = False
        
        self.centreCursorMNI152.enable = enable


    @actions.action
    def resetZoom(self):
        """Sets the :class:`.SceneOpts.zoom`, :class:`.OrthoOpts.xzoom`,
        :class:`.OrthoOpts.yzoom`,  and :class:`.OrthoOpts.zzoom` properties
        to 100%.
        """

        opts = self._viewPanel.getSceneOptions()

        opts.zoom  = 100
        opts.xzoom = 100
        opts.yzoom = 100
        opts.zzoom = 100


    @actions.action
    def centreCursor(self):
        """Sets the :attr:`.DisplayContext.location` to the centre of the
        :attr:`.DisplayContext.bounds`.
        """

        bounds = self._displayCtx.bounds

        xmid = bounds.xlo + 0.5 * bounds.xlen
        ymid = bounds.ylo + 0.5 * bounds.ylen
        zmid = bounds.zlo + 0.5 * bounds.zlen

        self._displayCtx.location.xyz = [xmid, ymid, zmid]


    @actions.action
    def centreCursorMNI152(self):
        """If the currently selected overlay is aligned to MNI152 space, sets
        the :attr:`.DisplayContext.location` to MNI152 location (0, 0, 0).
        """

        ovl  = self._displayCtx.getSelectedOverlay()
        opts = self._displayCtx.getOptx(ovl)

        origin = opts.transformCoords([0, 0, 0], 'world', 'display')

        self._displayCtx.location.xyz = origin


    ########################
    # Navigate mode handlers
    ########################

    
    def __offsetLocation(self, x, y, z):
        """Used by some ``nav`` mode handlers. Returns a sequence of three
        values, one per display space axis, which specify the amount by
        which the :attr:`.DisplayContext.location` should be changed,
        according to the directions specified by the ``x``, ``y``, and ``z``
        arguments.

        If the currently selected overlay is an :class:`.Nifti1` instance, the
        distance that a navigation operation should shift the display will
        differ depending on the value of the :attr:`.Nifti1Opts.transform`
        property. For example, if ``transform`` is ``id``, the display should
        be moved by one unit (which corresponds to one voxel). But if the
        ``transform`` is ``pixdim``, the display should be moved by one pixdim
        (e.g. 2, for a "math:`2mm^3` image).

        Each of the ``x``, ``y`` and ``z`` arguments are interpreted as being
        positive, zero, or negative. A positive/negative value indicates that
        the display location should be increased/decreased along the
        corresponding axis, and zero indicates that the location should stay
        the same along an axis.
        """
        
        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        # If non-zero, round to -1 or +1
        x = np.sign(x) * np.ceil(np.abs(np.clip(x, -1, 1)))
        y = np.sign(y) * np.ceil(np.abs(np.clip(y, -1, 1)))
        z = np.sign(z) * np.ceil(np.abs(np.clip(z, -1, 1)))

        # If the currently selected overlay
        # is non-volumetric, and does not
        # have a reference image, we'll just
        # move by +/-1 along each axis (as
        # specified by the x/y/z parameters).
        if overlay is None:
            dloc     = self._displayCtx.location.xyz
            dloc[0] += x
            dloc[1] += y
            dloc[2] += z

        # But if we have a voluemtric reference
        # image to play with, we're going to
        # move to the next/previous voxel along
        # each axis (as specified by x/y/z),
        # and calculate the corresponding location
        # in display space coordinates.
        else:

            # We use this complicated looking
            # code so that the adjusted location
            # is centered within the next/previous
            # voxel on the depth axis.
            # 
            # The procedure is as follows:
            # 
            #   1. Calculate the current display
            #      location in voxels. If we are
            #      displaying in id/pixdim space,
            #      we round the voxels to integers,
            #      otherwise we use floating point
            #      voxel coordinates.
            #       
            #   2. Offset the voxel coordinates
            #      according to the x/y/z parameters. To
            #      do this we use the Image.axisMapping
            #      method which returns the approximate
            #      correspondence between voxel axes and
            #      display axes.
            #
            #   3. Transform the voxel coordinates back
            #      into the display coordinate system.

            offsets  = [x, y, z]
            opts     = self._displayCtx.getOpts(overlay)
            vround   = opts.transform in ('id', 'pixdim')
            vloc     = opts.getVoxel(clip=False, vround=vround)
            voxAxes  = overlay.axisMapping(opts.getTransform('voxel',
                                                             'display'))

            for i in range(3):
                vdir       = np.sign(voxAxes[i])
                vax        = np.abs(voxAxes[i]) - 1
                vloc[vax] += vdir * offsets[i]

            dloc = opts.transformCoords([vloc], 'voxel', 'display')[0]

        return dloc


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
        """

        if len(self._overlayList) == 0:
            return

        try:    ch = chr(key)
        except: ch = None

        dirs = [0, 0, 0]

        if   key == wx.WXK_LEFT:  dirs[canvas.xax] = -1
        elif key == wx.WXK_RIGHT: dirs[canvas.xax] =  1
        elif key == wx.WXK_UP:    dirs[canvas.yax] =  1
        elif key == wx.WXK_DOWN:  dirs[canvas.yax] = -1
        elif ch  in ('+', '='):   dirs[canvas.zax] =  1
        elif ch  in ('-', '_'):   dirs[canvas.zax] = -1

        def update():
            self._displayCtx.location.xyz = self.__offsetLocation(*dirs)

        # See comment in _zoomModeMouseWheel about timeout
        async.idle(update, timeout=0.1)

        
    #####################
    # Slice mode handlers
    #####################

    
    def _sliceModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Handles mouse wheel movement in ``nav`` mode.

        Mouse wheel movement on a canvas changes the depth location displayed
        on that canvas.
        """

        if len(self._overlayList) == 0:
            return

        dirs = [0, 0, 0]

        if   wheel > 0: dirs[canvas.zax] = -1
        elif wheel < 0: dirs[canvas.zax] =  1

        pos = self.__offsetLocation(*dirs)

        def update():
            self._displayCtx.location[canvas.zax] = pos[canvas.zax]

        # See comment in _zoomModeMouseWheel about timeout
        async.idle(update, timeout=0.1)

        
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

        # Over SSH/X11, mouse wheel events seem to get queued,
        # and continue to get processed after the user has
        # stopped spinning the mouse wheel, which is super
        # frustrating. So we do the update asynchronously, and
        # set a time out to drop the event, and prevent the
        # horribleness from happening.
        def update():
            canvas.zoom += wheel
        
        async.idle(update, timeout=0.1)

        
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

        self._zoomModeMouseWheel(None, canvas, zoom)

        
    def _zoomModeRightMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles right mouse drags in ``zoom`` mode.

        Right mouse drags in zoom mode draw a rectangle on the target
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

        
    def _zoomModeRightMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles right mouse up events in ``zoom`` mode.

        When the right mouse is released in zoom mode, the target
        canvas is zoomed in to the rectangle region that was drawn by the
        user.
        """

        if canvasPos is None:
            return

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()
        
        if mouseDownPos  is None or \
           canvasDownPos is None:
            return

        if self.__lastRect is not None:
            canvas.getAnnotations().dequeue(self.__lastRect)
            self.__lastRect = None

        xlo = min(canvasPos[canvas.xax], canvasDownPos[canvas.xax])
        xhi = max(canvasPos[canvas.xax], canvasDownPos[canvas.xax])
        ylo = min(canvasPos[canvas.yax], canvasDownPos[canvas.yax])
        yhi = max(canvasPos[canvas.yax], canvasDownPos[canvas.yax])

        canvas.zoomTo(xlo, xhi, ylo, yhi)
        
        
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

        def update():
            canvas.panDisplayBy(xoff, yoff)

        # See comment in _zoomModeMouseWheel about timeout
        async.idle(update, timeout=0.1)


    #############
    # Bricon mode
    #############


    def _briconModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles left mouse drags in ``bricon`` mode.

        The brightness and contrast of the currently selected overlay are
        adjusted according to the location of the mouse, relative to the
        canvas.
        """

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return 

        display = self._displayCtx.getDisplay(overlay)
        w, h    = canvas.GetSize().Get()
        x, y    = mousePos

        brightness = float(x) / w
        contrast   = float(y) / h

        log.debug('Adjusting bricon for {} '
                  '(brightness: {}, contrast: {})'.format(
                      overlay.name,
                      brightness,
                      contrast))

        display.brightness = 100 * brightness
        display.contrast   = 100 * contrast
