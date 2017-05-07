#!/usr/bin/env python
#
# slicecanvas.py - The SliceCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SliceCanvas` class, which contains the
functionality to display a 2D slice from a collection of 3D overlays.
"""


import copy
import logging

import OpenGL.GL as gl

import numpy as np

import fsl.data.image                     as fslimage
import fsl.utils.async                    as async
import fsleyes_widgets.utils.status       as status
import fsleyes_props                      as props

import fsleyes.strings                    as strings
import fsleyes.displaycontext.canvasopts  as canvasopts
import fsleyes.gl.routines                as glroutines
import fsleyes.gl.resources               as glresources
import fsleyes.gl.globject                as globject
import fsleyes.gl.textures                as textures
import fsleyes.gl.annotations             as annotations


log = logging.getLogger(__name__)


class SliceCanvas(props.HasProperties):
    """The ``SliceCanvas`` represents a canvas which may be used to display a
    single 2D slice from a collection of 3D overlays.  See also the
    :class:`.LightBoxCanvas`, a sub-class of ``SliceCanvas``.


    .. note:: The :class:`SliceCanvas` class is not intended to be instantiated
              directly - use one of these subclasses, depending on your
              use-case:

               - :class:`.OSMesaSliceCanvas` for static off-screen rendering of
                 a scene using OSMesa.

               - :class:`.WXGLSliceCanvas` for interactive rendering on a
                 :class:`wx.glcanvas.GLCanvas` canvas.


    The ``SliceCanvas`` derives from the :class:`.props.HasProperties` class.
    The settings, and current scene displayed on a ``SliceCanvas`` instance,
    can be changed through the properties of the ``SliceCanvas``. All of these
    properties are defined in the :class:`.SliceCanvasOpts` class.


    **GL objects**


    The ``SliceCanvas`` draws :class:`.GLObject` instances. When created, a
    ``SliceCanvas`` creates a :class:`.GLObject` instance for every overlay in
    the :class:`.OverlayList`. When an overlay is added or removed, it
    creates/destroys ``GLObject`` instances accordingly.  Furthermore,
    whenever the :attr:`.Display.overlayType` for an existing overlay
    changes, the ``SliceCanvas`` destroys the old ``GLObject`` associated with
    the overlay, and creates a new one.


    The ``SliceCanvas`` also uses an :class:`.Annotations` instance, for
    drawing simple annotations on top of the overlays.  This ``Annotations``
    instance can be accessed with the :meth:`getAnnotations` method.


    **Performance optimisations**


    The :attr:`renderMode` property controls the way in which the
    ``SliceCanvas`` renders :class:`.GLObject` instances. It has three
    settings:


    ============= ============================================================
    ``onscreen``  ``GLObject`` instances are rendered directly to the canvas.

    ``offscreen`` ``GLObject`` instances are rendered off-screen to a fixed
                  size 2D texture (a :class:`.RenderTexture`). This texture
                  is then rendered to the canvas. One :class:`.RenderTexture`
                  is used for every overlay  in the :class:`.OverlayList`.

    ``prerender`` A stack of 2D slices for every ``GLObject`` instance is
                  pre-generated off-screen, and cached, using a
                  :class:`.RenderTextureStack`. When the ``SliceCanvas`` needs
                  to display a particular Z location, it retrieves the
                  appropriate slice from the stack, and renders it to the
                  canvas. One :class:`.RenderTextureStack` is used for every
                  overlay in the :class:`.OverlayList`.
    ============= ============================================================


    **Attributes and methods**


    The following attributes are available on a ``SliceCanvas``:


    =============== ==========================================
    ``xax``         Index of the horizontal screen axis
    ``yax``         Index of the horizontal screen axis
    ``zax``         Index of the horizontal screen axis
    ``name``        A unique name for this ``SliceCanvas``
    ``overlayList`` Reference to the :class:`.OverlayList`.
    ``displayCtx``  Reference to the :class:`.DisplayContext`.
    =============== ==========================================


    The following convenience methods are available on a ``SliceCanvas``:

    .. autosummary::
       :nosignatures:

       canvasToWorld
       panDisplayBy
       centreDisplayAt
       panDisplayToShow
       zoomTo
       resetDisplay
       getAnnotations
    """


    pos             = copy.copy(canvasopts.SliceCanvasOpts.pos)
    zoom            = copy.copy(canvasopts.SliceCanvasOpts.zoom)
    displayBounds   = copy.copy(canvasopts.SliceCanvasOpts.displayBounds)
    showCursor      = copy.copy(canvasopts.SliceCanvasOpts.showCursor)
    cursorGap       = copy.copy(canvasopts.SliceCanvasOpts.cursorGap)
    zax             = copy.copy(canvasopts.SliceCanvasOpts.zax)
    invertX         = copy.copy(canvasopts.SliceCanvasOpts.invertX)
    invertY         = copy.copy(canvasopts.SliceCanvasOpts.invertY)
    cursorColour    = copy.copy(canvasopts.SliceCanvasOpts.cursorColour)
    bgColour        = copy.copy(canvasopts.SliceCanvasOpts.bgColour)
    renderMode      = copy.copy(canvasopts.SliceCanvasOpts.renderMode)


    def __init__(self, overlayList, displayCtx, zax=0):
        """Create a ``SliceCanvas``.

        :arg overlayList: An :class:`.OverlayList` object containing a
                          collection of overlays to be displayed.

        :arg displayCtx:  A :class:`.DisplayContext` object which describes
                          how the overlays should be displayed.

        :arg zax:         Display coordinate system axis perpendicular to the
                          plane to be displayed (the *depth* axis), default 0.
        """

        props.HasProperties.__init__(self)

        self.overlayList = overlayList
        self.displayCtx  = displayCtx
        self.name        = '{}_{}'.format(self.__class__.__name__, id(self))

        # A GLObject instance is created for
        # every overlay in the overlay list,
        # and stored in this dictionary
        self._glObjects = {}

        # If render mode is offscren or prerender, these
        # dictionaries will contain a RenderTexture or
        # RenderTextureStack instance for each overlay in
        # the overlay list. These dictionaries are
        # respectively of the form:
        #     { overlay : RenderTexture              }
        #     { overlay : (RenderTextureStack, name) }
        #
        self._offscreenTextures = {}
        self._prerenderTextures = {}

        # The zax property is the image axis which maps to the
        # 'depth' axis of this canvas. The _zAxisChanged method
        # also fixes the values of 'xax' and 'yax'.
        self.zax = zax
        self.xax = (zax + 1) % 3
        self.yax = (zax + 2) % 3

        self._annotations = annotations.Annotations(self, self.xax, self.yax)

        # when any of the properties of this
        # canvas change, we need to redraw
        self.addListener('zax',           self.name, self._zAxisChanged)
        self.addListener('pos',           self.name, self.Refresh)
        self.addListener('displayBounds', self.name, self.Refresh)
        self.addListener('bgColour',      self.name, self.Refresh)
        self.addListener('cursorColour',  self.name, self.Refresh)
        self.addListener('showCursor',    self.name, self.Refresh)
        self.addListener('cursorGap',     self.name, self.Refresh)
        self.addListener('invertX',       self.name, self.Refresh)
        self.addListener('invertY',       self.name, self.Refresh)
        self.addListener('zoom',          self.name, self._zoomChanged)
        self.addListener('renderMode',    self.name, self._renderModeChange)

        # When the overlay list changes, refresh the
        # display, and update the display bounds
        self.overlayList.addListener('overlays',
                                     self.name,
                                     self._overlayListChanged)
        self.displayCtx .addListener('overlayOrder',
                                     self.name,
                                     self.Refresh)
        self.displayCtx .addListener('bounds',
                                     self.name,
                                     self._overlayBoundsChanged)
        self.displayCtx .addListener('syncOverlayDisplay',
                                     self.name,
                                     self._syncOverlayDisplayChanged)

        # The zAxisChanged method
        # will kick everything off
        self._zAxisChanged()


    def destroy(self):
        """This method must be called when this ``SliceCanvas`` is no longer
        being used.

        It removes listeners from all :class:`.OverlayList`,
        :class:`.DisplayContext`, and :class:`.Display` instances, and
        destroys OpenGL representations of all overlays.
        """
        self.removeListener('zax',             self.name)
        self.removeListener('pos',             self.name)
        self.removeListener('displayBounds',   self.name)
        self.removeListener('showCursor',      self.name)
        self.removeListener('invertX',         self.name)
        self.removeListener('invertY',         self.name)
        self.removeListener('zoom',            self.name)
        self.removeListener('renderMode',      self.name)

        self.overlayList.removeListener('overlays',     self.name)
        self.displayCtx .removeListener('bounds',       self.name)
        self.displayCtx .removeListener('overlayOrder', self.name)

        for overlay in self.overlayList:
            disp  = self.displayCtx.getDisplay(overlay)
            globj = self._glObjects.get(overlay)

            disp.removeListener('overlayType',  self.name)
            disp.removeListener('enabled',      self.name)

            # globj could be None, or could
            # be False - see genGLObject.
            if globj:
                globj.deregister(self.name)
                globj.destroy()

            rt, rtName = self._prerenderTextures.get(overlay, (None, None))
            ot         = self._offscreenTextures.get(overlay, None)

            if rt is not None: glresources.delete(rtName)
            if ot is not None: ot         .destroy()

        self.overlayList        = None
        self.displayCtx         = None
        self._glObjects         = None
        self._prerenderTextures = None
        self._offscreenTextures = None


    def destroyed(self):
        """Returns ``True`` if a call to :meth:`destroy` has been made,
        ``False`` otherwise.
        """
        return self.overlayList is None


    def canvasToWorld(self, xpos, ypos, invertX=None, invertY=None):
        """Given pixel x/y coordinates on this canvas, translates them
        into xyz display coordinates.

        :arg invertX: If ``None``, taken from :attr:`.invertX`.
        :arg invertY: If ``None``, taken from :attr:`.invertY`.
        """

        if invertX is None: invertX = self.invertX
        if invertY is None: invertY = self.invertY

        realWidth                 = self.displayBounds.xlen
        realHeight                = self.displayBounds.ylen
        canvasWidth, canvasHeight = [float(s) for s in self._getSize()]

        if invertX: xpos = canvasWidth  - xpos
        if invertY: ypos = canvasHeight - ypos

        if realWidth    == 0 or \
           canvasWidth  == 0 or \
           realHeight   == 0 or \
           canvasHeight == 0:
            return None

        xpos = self.displayBounds.xlo + (xpos / canvasWidth)  * realWidth
        ypos = self.displayBounds.ylo + (ypos / canvasHeight) * realHeight

        pos = [None] * 3
        pos[self.xax] = xpos
        pos[self.yax] = ypos
        pos[self.zax] = self.pos.z

        return pos


    def panDisplayBy(self, xoff, yoff):
        """Pans the canvas display by the given x/y offsets (specified in
        display coordinates).
        """

        if len(self.overlayList) == 0: return

        xmin, xmax, ymin, ymax = self.displayBounds[:]

        xmin = xmin + xoff
        xmax = xmax + xoff
        ymin = ymin + yoff
        ymax = ymax + yoff

        self.displayBounds[:] = [xmin, xmax, ymin, ymax]


    def centreDisplayAt(self, xpos, ypos):
        """Pans the display so the given x/y position is in the centre. """

        xcentre, ycentre = self.getDisplayCentre()
        self.panDisplayBy(xpos - xcentre, ypos - ycentre)


    def getDisplayCentre(self):
        """Returns the horizontal/vertical position, in display coordinates,
        of the current centre of the display bounds.
        """
        bounds  = self.displayBounds
        xcentre = bounds.xlo + (bounds.xhi - bounds.xlo) * 0.5
        ycentre = bounds.ylo + (bounds.yhi - bounds.ylo) * 0.5

        return xcentre, ycentre


    def panDisplayToShow(self, xpos, ypos):
        """Pans the display so that the given x/y position (in display
        coordinates) is visible.
        """

        bounds = self.displayBounds

        # Do nothing if the position
        # is already being displayed
        if xpos >= bounds.xlo and xpos <= bounds.xhi and \
           ypos >= bounds.ylo and ypos <= bounds.yhi: return

        xoff = 0
        yoff = 0

        if   xpos <= bounds.xlo: xoff = xpos - bounds.xlo
        elif xpos >= bounds.xhi: xoff = xpos - bounds.xhi

        if   ypos <= bounds.ylo: yoff = ypos - bounds.ylo
        elif ypos >= bounds.yhi: yoff = ypos - bounds.yhi

        if xoff != 0 or yoff != 0:
            self.panDisplayBy(xoff, yoff)


    def zoomTo(self, xlo, xhi, ylo, yhi):
        """Zooms the canvas to the given rectangle, specified in
        horizontal/vertical display coordinates.
        """

        # We are going to convert the rectangle specified by
        # the inputs into a zoom value, set the canvas zoom
        # level, and then centre the canvas on the rectangle.

        # Middle of the rectangle, used
        # at the end for centering
        xmid = xlo + (xhi - xlo) / 2.0
        ymid = ylo + (yhi - ylo) / 2.0

        # Size of the rectangle
        rectXlen = abs(xhi - xlo)
        rectYlen = abs(yhi - ylo)

        if rectXlen == 0: return
        if rectYlen == 0: return

        # Size of the overlay bounding
        # box, and the zoom value limits
        xmin, xmax = self.displayCtx.bounds.getRange(self.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(self.yax)
        zoommin    = self.getConstraint('zoom', 'minval')
        zoommax    = self.getConstraint('zoom', 'maxval')

        xlen    = xmax    - xmin
        ylen    = ymax    - ymin
        zoomlen = zoommax - zoommin

        # Calculate the ratio of the
        # rectangle to the canvas limits
        xratio = rectXlen / xlen
        yratio = rectYlen / ylen
        ratio  = max(xratio, yratio)

        # Calculate the zoom from this ratio -
        # this is the inverse of the zoom->canvas
        # bounds calculation, as implemented in
        # _applyZoom.
        zoom  = zoommin / ratio
        zoom  = ((zoom - zoommin) / zoomlen) ** (1.0 / 3.0)
        zoom  = zoommin + zoom * zoomlen

        # Update the zoom value, call updateDisplayBounds
        # to apply the new zoom to the display bounds,
        # then centre the display on the calculated
        # centre point.
        with props.skip(self, 'zoom',          self.name), \
             props.skip(self, 'displayBounds', self.name):
            self.zoom = zoom
            self._updateDisplayBounds()
            self.centreDisplayAt(xmid, ymid)

        self.Refresh()


    def resetDisplay(self):
        """Resets the :attr:`zoom` to 100%, and sets the canvas display
        bounds to the overaly bounding box (from the
        :attr:`.DisplayContext.bounds`)
        """

        xmin = self.displayCtx.bounds.getLo(self.xax)
        xmax = self.displayCtx.bounds.getHi(self.xax)
        ymin = self.displayCtx.bounds.getLo(self.yax)
        ymax = self.displayCtx.bounds.getHi(self.yax)

        with props.skip(self, 'zoom', self.name):
            self.zoom = 100

        with props.suppress(self, 'displayBounds'):
            self._updateDisplayBounds((xmin, xmax, ymin, ymax))

        self.Refresh()


    def getAnnotations(self):
        """Returns an :class:`.Annotations` instance, which can be used to
        annotate the canvas.
        """
        return self._annotations


    def getGLObject(self, overlay):
        """Returns the :class:`.GLObject` associated with the given
        ``overlay``, or ``None`` if there isn't one.
        """
        globj = self._glObjects.get(overlay, None)

        # globjs can be set to False
        if not globj: return None
        else:         return globj


    def _initGL(self):
        """Call the :meth:`_overlayListChanged` method - it will generate
        any necessary GL data for each of the overlays.
        """
        self._overlayListChanged()


    def _updateRenderTextures(self):
        """Called when the :attr:`renderMode` changes, when the overlay
        list changes, or when the  GLObject representation of an overlay
        changes.

        If the :attr:`renderMode` property is ``onscreen``, this method does
        nothing.

        Otherwise, creates/destroys :class:`.RenderTexture` or
        :class:`.RenderTextureStack` instances for newly added/removed
        overlays.
        """

        if self.renderMode == 'onscreen':
            return

        # If any overlays have been removed from the overlay
        # list, destroy the associated render texture stack
        if self.renderMode == 'offscreen':
            for ovl, texture in list(self._offscreenTextures.items()):
                if ovl not in self.overlayList:
                    self._offscreenTextures.pop(ovl)
                    texture.destroy()

        elif self.renderMode == 'prerender':
            for ovl, (texture, name) in list(self._prerenderTextures.items()):
                if ovl not in self.overlayList:
                    self._prerenderTextures.pop(ovl)
                    glresources.delete(name)

        # If any overlays have been added to the list,
        # create a new render textures for them
        for overlay in self.overlayList:

            if self.renderMode == 'offscreen':
                if overlay in self._offscreenTextures:
                    continue

            elif self.renderMode == 'prerender':
                if overlay in self._prerenderTextures:
                    continue

            globj   = self._glObjects.get(overlay, None)
            display = self.displayCtx.getDisplay(overlay)

            if not globj:
                continue

            # For offscreen render mode, GLObjects are
            # first rendered to an offscreen texture,
            # and then that texture is rendered to the
            # screen. The off-screen texture is managed
            # by a RenderTexture object.
            if self.renderMode == 'offscreen':

                name = '{}_{}_{}'.format(display.name, self.xax, self.yax)
                rt   = textures.GLObjectRenderTexture(
                    name,
                    globj,
                    self.xax,
                    self.yax)

                self._offscreenTextures[overlay] = rt

            # For prerender mode, slices of the
            # GLObjects are pre-rendered on a
            # stack of off-screen textures, which
            # is managed by a RenderTextureStack
            # object.
            elif self.renderMode == 'prerender':
                rt, name = self._getPreRenderTexture(globj, overlay)
                self._prerenderTextures[overlay] = rt, name

        self.Refresh()


    def _getPreRenderTexture(self, globj, overlay):
        """Creates/retrieves a :class:`.RenderTextureStack` for the given
        :class:`.GLObject`. A tuple containing the ``RenderTextureStack``,
        and its name, as passed to the :mod:`.resources` module, is returned.

        :arg globj:   The :class:`.GLObject` instance.
        :arg overlay: The overlay object.
        """

        display = self.displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        name = '{}_{}_zax{}'.format(
            id(overlay),
            textures.RenderTextureStack.__name__,
            self.zax)

        # If all display/opts properties
        # are synchronised to the parent,
        # then we use a texture stack that
        # might be shared across multiple
        # views.
        #
        # But if any display/opts properties
        # are not synchronised, we'll use our
        # own texture stack.
        if not (display.getParent()         and
                display.allSyncedToParent() and
                opts   .getParent()         and
                opts   .allSyncedToParent()):

            name = '{}_{}'.format(id(self.displayCtx), name)

        if glresources.exists(name):
            rt = glresources.get(name)

        else:
            rt = textures.RenderTextureStack(globj)
            rt.setAxes(self.xax, self.yax)
            glresources.set(name, rt)

        return rt, name


    def _renderModeChange(self, *a):
        """Called when the :attr:`renderMode` property changes."""

        log.debug('Render mode changed: {}'.format(self.renderMode))

        # destroy any existing render textures
        for ovl, texture in list(self._offscreenTextures.items()):
            self._offscreenTextures.pop(ovl)
            texture.destroy()

        for ovl, (texture, name) in list(self._prerenderTextures.items()):
            self._prerenderTextures.pop(ovl)
            glresources.delete(name)

        # Onscreen rendering - each GLObject
        # is rendered directly to the canvas
        # displayed on the screen, so render
        # textures are not needed.
        if self.renderMode == 'onscreen':
            self.Refresh()
            return

        # Off-screen or prerender rendering - update
        # the render textures for every GLObject
        self._updateRenderTextures()


    def _syncOverlayDisplayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.syncOverlayDisplay`
        property changes. If the current :attr:`renderMode` is ``prerender``,
        the :class:`.RenderTextureStack` instances for each overlay are
        re-created.

        This is done because, if all display properties for an overlay are
        synchronised, then a single ``RenderTextureStack`` can be shared
        across multiple displays. However, if any display properties are not
        synchronised, then a separate ``RenderTextureStack`` is needed for
        the :class:`.DisplayContext` used by this ``SliceCanvas``.
        """
        if self.renderMode == 'prerender':
            self._renderModeChange(self)


    def _zAxisChanged(self, *a):
        """Called when the :attr:`zax` property is changed. Calculates
        the corresponding X and Y axes, and saves them as attributes of
        this object. Also notifies the GLObjects for every overlay in
        the overlay list.
        """

        log.debug('{}'.format(self.zax))

        # Store the canvas position, in the
        # axis order of the display coordinate
        # system
        pos                  = [None] * 3
        pos[self.xax]        = self.pos.x
        pos[self.yax]        = self.pos.y
        pos[pos.index(None)] = self.pos.z

        # Figure out the new x and y axes
        # based on the new zax value
        dims = list(range(3))
        dims.pop(self.zax)
        self.xax = dims[0]
        self.yax = dims[1]

        self._annotations.setAxes(self.xax, self.yax)

        for ovl, globj in list(self._glObjects.items()):
            if globj:
                globj.setAxes(self.xax, self.yax)

        self._overlayBoundsChanged()

        # Reset the canvas position as, because the
        # z axis has been changed, the old coordinates
        # will be in the wrong dimension order
        self.pos.xyz = [pos[self.xax],
                        pos[self.yax],
                        pos[self.zax]]

        # If pre-rendering is enabled, the
        # render textures need to be updated, as
        # they are configured in terms of the
        # display axes. Easiest way to do this
        # is to destroy and re-create them
        self._renderModeChange()


    def __overlayTypeChanged(self, value, valid, display, name):
        """Called when the :attr:`.Display.overlayType` setting for any
        overlay changes. Makes sure that an appropriate :class:`.GLObject`
        has been created for the overlay (see the :meth:`__genGLObject`
        method).
        """

        log.debug('GLObject representation for {} '
                  'changed to {}'.format(display.name,
                                         display.overlayType))

        self.__regenGLObject(display.getOverlay())
        self.Refresh()


    def __regenGLObject(self,
                        overlay,
                        updateRenderTextures=True,
                        refresh=True):
        """Destroys any existing :class:`.GLObject` associated with the given
        ``overlay``, and creates a new one (via the :meth:`__genGLObject`
        method).

        If ``updateRenderTextures`` is ``True`` (the default), and the
        :attr:`.renderMode` is ``offscreen`` or ``prerender``, any
        render texture associated with the overlay is destroyed.
        """

        # Tell the previous GLObject (if
        # any) to clean up after itself
        globj = self._glObjects.pop(overlay, None)
        if globj:
            globj.deregister(self.name)
            globj.destroy()

            if updateRenderTextures:
                if self.renderMode == 'offscreen':
                    tex = self._offscreenTextures.pop(overlay, None)
                    if tex is not None:
                        tex.destroy()

                elif self.renderMode == 'prerender':
                    tex, name = self._prerenderTextures.pop(
                        overlay, (None, None))
                    if tex is not None:
                        glresources.delete(name)

        self.__genGLObject(overlay, updateRenderTextures, refresh)


    def __genGLObject(self, overlay, updateRenderTextures=True, refresh=True):
        """Creates a :class:`.GLObject` instance for the given ``overlay``.
        Does nothing if a ``GLObject`` already exists for the given overlay.

        If ``updateRenderTextures`` is ``True`` (the default), and the
        :attr:`.renderMode` is ``offscreen`` or ``prerender``, any
        textures for the overlay are updated.

        If ``refresh`` is ``True`` (the default), the :meth:`Refresh` method
        is called after the ``GLObject`` has been created.

        .. note:: If running in ``wx`` (i.e. via a :class:`.WXGLSliceCanvas`),
                  the :class:`.GLObject` instnace will be created on the
                  ``wx.EVT_IDLE`` lopp (via the :mod:`.idle` module).
        """

        display = self.displayCtx.getDisplay(overlay)

        if overlay in self._glObjects:
            return

        # We put a placeholder value in
        # the globjects dictionary, so
        # that the _draw method knows
        # that creation for this overlay
        # is pending.
        self._glObjects[overlay] = False

        def create():

            if not self or self.destroyed():
                return

            # The overlay has been removed from the
            # globjects dictionary between the time
            # the pending flag was set above, and
            # the time that this create() call was
            # executed. Possibly because the overlay
            # was removed between these two events.
            # All is well, just ignore it.
            if overlay not in self._glObjects:
                return

            # We need a GL context to create a new GL
            # object. If we can't get it now, the GL
            # object creation will be re-scheduled on
            # the next call to _draw (via _getGLObjects).
            if not self._setGLContext():

                # Clear the pending flag so
                # this GLObject creation
                # gets re-scheduled.
                self._glObjects.pop(overlay)
                return

            globj = globject.createGLObject(overlay,
                                            display,
                                            self.xax,
                                            self.yax)

            if globj is not None:
                globj.register(self.name, self.__onGLObjectUpdate)

                # A hack which allows us to easily
                # retrieve the overlay associated
                # with a given GLObject. See the
                # __onGLObjectUpdate method.
                globj._sc_overlay = overlay

            self._glObjects[overlay] = globj

            if updateRenderTextures:
                self._updateRenderTextures()

            display.addListener('overlayType',
                                self.name,
                                self.__overlayTypeChanged,
                                overwrite=True)

            display.addListener('enabled',
                                self.name,
                                self.Refresh,
                                overwrite=True)

            if refresh:
                self.Refresh()

        create = status.reportErrorDecorator(
            strings.titles[  self, 'globjectError'],
            strings.messages[self, 'globjectError'].format(overlay.name))(
                create)

        async.idle(create)


    def __onGLObjectUpdate(self, globj, *a):
        """Called when a :class:`.GLObject` has been updated, and needs to be
        redrawn.
        """

        # If we are in prerender mode, we
        # need to tell the RenderTextureStack
        # for this GLObject to update itself.
        if self.renderMode == 'prerender':

            overlay  = globj._sc_overlay
            rt, name = self._prerenderTextures.get(overlay, (None, None))

            if rt is not None:
                rt.onGLObjectUpdate()

        self.Refresh()


    def _overlayListChanged(self, *args, **kwargs):
        """This method is called every time an overlay is added or removed
        to/from the overlay list.

        For newly added overlays, calls the :meth:`__genGLObject` method,
        which initialises the OpenGL data necessary to render the
        overlay.
        """

        # Destroy any GL objects for overlays
        # which are no longer in the list
        for ovl, globj in list(self._glObjects.items()):
            if ovl not in self.overlayList:
                self._glObjects.pop(ovl)
                if globj:
                    globj.destroy()

        # Create a GL object for any new overlays,
        # and attach a listener to their display
        # properties so we know when to refresh
        # the canvas.
        for overlay in self.overlayList:

            # A GLObject already exists
            # for this overlay
            if overlay in self._glObjects:
                continue

            self.__regenGLObject(overlay,
                                 updateRenderTextures=False,
                                 refresh=False)

        # All the GLObjects are created using
        # async.idle, so we call refresh in the
        # same way to make sure it gets called
        # after all the GLObject creations.
        def refresh():

            # This SliceCanvas might get
            # destroyed before this idle
            # task is executed
            if not self or self.destroyed():
                return

            self._updateRenderTextures()
            self.Refresh()

        async.idle(refresh)


    def _getGLObjects(self):
        """Called by :meth:`_draw`. Builds a list of all :class:`.GLObjects`
        to be drawn.

        :returns: A list of overlays, and a list of corresponding
                  :class:`.GLObjects` to be drawn.
        """

        overlays = []
        globjs   = []
        for ovl in self.displayCtx.getOrderedOverlays():

            globj = self._glObjects.get(ovl, None)

            # If an overlay does not yet have a corresponding
            # GLObject, we presume that it hasn't been created
            # yet, so we'll tell genGLObject to create one for
            # it.
            if   globj is None: self.__genGLObject(ovl)

            # If there is a value for this overlay in
            # the globjects dictionary, but it evaluates
            # to False, then GLObject creation has been
            # scheduled for the overlay - see genGLObject.
            elif globj:
                overlays.append(ovl)
                globjs  .append(globj)

        return overlays, globjs


    def _overlayBoundsChanged(self, *a):
        """Called when the display bounds are changed.

        Updates the constraints on the :attr:`pos` property so it is
        limited to stay within a valid range, and then calls the
        :meth:`resetDisplay` method.
        """

        ovlBounds = self.displayCtx.bounds

        with props.suppress(self, 'pos'):
            self.pos.setMin(0, ovlBounds.getLo(self.xax))
            self.pos.setMax(0, ovlBounds.getHi(self.xax))
            self.pos.setMin(1, ovlBounds.getLo(self.yax))
            self.pos.setMax(1, ovlBounds.getHi(self.yax))
            self.pos.setMin(2, ovlBounds.getLo(self.zax))
            self.pos.setMax(2, ovlBounds.getHi(self.zax))

        self.resetDisplay()


    def _zoomChanged(self, *a):
        """Called when the :attr:`zoom` property changes. Updates the
        display bounds.
        """
        loc = [self.displayCtx.location[self.xax],
               self.displayCtx.location[self.yax]]
        self._updateDisplayBounds(oldLoc=loc)


    def _applyZoom(self, xmin, xmax, ymin, ymax):
        """*Zooms* in to the given rectangle according to the current value
        of the zoom property Returns a 4-tuple containing the updated bound
        values.
        """

        # Zoom is specified as a percentage.
        # At 100% the full scene takes up the
        # full display.
        #
        # In order to make the zoom smoother
        # at low levels, we re-scale the zoom
        # value to be exponential across the
        # range.
        #
        # This is done by transforming the zoom
        # from [100 - zmax] into [0.0 - 1.0], then
        # turning it from linear [0.0 - 1.0] to
        # exponential [0.0 - 1.0], and then finally
        # transforming it back to [100 - zmax].
        #
        # HOWEVER there is a slight hack in that,
        # if the zoom value is less than 100%, it
        # will be applied linearly (i.e. 50% will
        # cause the scene to take up 50% of the
        # screen)

        # Assuming that minval == 100.0
        zoom    = self.zoom
        minzoom = self.getConstraint('zoom', 'minval')
        maxzoom = self.getConstraint('zoom', 'maxval')

        # Don't break the maths below
        if zoom <= 0:
            zoom = 1

        # Normal behaviour
        if zoom >= 100:

            # [100 - zmax] -> [0.0 - 1.0] -> exponentify -> [100 - zmax]
            zoom       = (self.zoom - minzoom) / (maxzoom - minzoom)
            zoom       = minzoom + (zoom ** 3) * (maxzoom - minzoom)

            # Then we transform the zoom from
            # [100 - zmax] to [1.0 - 0.0] -
            # this value is used to scale the
            # bounds.
            zoomFactor = minzoom / zoom

        # Hack for zoom < 100
        else:
            zoomFactor = 100.0 / zoom

        xlen    = xmax - xmin
        ylen    = ymax - ymin
        newxlen = xlen * zoomFactor
        newylen = ylen * zoomFactor

        # centre the zoomed-in rectangle
        # on the provided limits
        xmid = xmin + 0.5 * xlen
        ymid = ymin + 0.5 * ylen

        # new x/y min/max bounds
        xmin = xmid - 0.5 * newxlen
        xmax = xmid + 0.5 * newxlen
        ymin = ymid - 0.5 * newylen
        ymax = ymid + 0.5 * newylen

        return (xmin, xmax, ymin, ymax)


    def _updateDisplayBounds(self, bbox=None, oldLoc=None):
        """Called on canvas resizes, overlay bound changes, and zoom changes.

        Calculates the bounding box, in display coordinates, to be displayed
        on the canvas. Stores this bounding box in the :attr:`displayBounds`
        property. If any of the parameters are not provided, the
        :attr:`.DisplayContext.bounds` are used.


        .. note:: This method is used internally, and also by the
                  :class:`.WXGLSliceCanvas` class.

        .. warning:: This code assumes that, if the display coordinate system
                     has changed, the display context location has already
                     been updated.  See the
                     :meth:`.DisplayContext.__displaySpaceChanged` method.


        :arg bbox:   Tuple containing four values:

                      - Minimum x (horizontal) value to be in the display
                        bounds.

                      - Maximum x value to be in the display bounds.

                      - Minimum y (vertical) value to be in the display bounds.

                      - Maximum y value to be in the display bounds.

        :arg oldLoc: If provided, should be the ``(x, y)`` location shown on
                     this ``SliceCanvas`` - the new display bounds will be
                     adjusted so that this location remains the same, with
                     respect to the new field of view.
        """

        if bbox is None:
            bbox = (self.displayCtx.bounds.getLo(self.xax),
                    self.displayCtx.bounds.getHi(self.xax),
                    self.displayCtx.bounds.getLo(self.yax),
                    self.displayCtx.bounds.getHi(self.yax))

        xmin = bbox[0]
        xmax = bbox[1]
        ymin = bbox[2]
        ymax = bbox[3]

        # Save the display bounds in case
        # we need to preserve them with
        # respect to the current display
        # location.
        width, height                      = self._getSize()
        oldxmin, oldxmax, oldymin, oldymax = self.displayBounds[:]

        log.debug('{}: Required display bounds: '
                  'X: ({: 5.1f}, {: 5.1f}) Y: ({: 5.1f}, {: 5.1f})'.format(
                      self.zax, xmin, xmax, ymin, ymax))

        # Adjust the bounds to preserve the
        # x/y aspect ratio, and according to
        # the current zoom level.
        xmin, xmax, ymin, ymax = glroutines.preserveAspectRatio(
            width, height, xmin, xmax, ymin, ymax)
        xmin, xmax, ymin, ymax = self._applyZoom(xmin, xmax, ymin, ymax)

        # If a location (oldLoc) has been provided,
        # adjust the bounds so they are consistent
        # with respect to that location.
        if oldLoc and (oldxmax > oldxmin) and (oldymax > oldymin):

            # Calculate the normalised distance from the
            # old cursor location to the old bound corner
            oldxoff = (oldLoc[0] - oldxmin) / (oldxmax - oldxmin)
            oldyoff = (oldLoc[1] - oldymin) / (oldymax - oldymin)

            # Re-set the new bounds to the current
            # display location, offset by the same
            # amount that it used to be (as
            # calculated above).
            #
            # N.B. This code assumes that, if the display
            #      coordinate system has changed, the display
            #      context location has already been updated.
            #      See the DisplayContext.__displaySpaceChanged
            #      method.
            xloc = self.displayCtx.location[self.xax]
            yloc = self.displayCtx.location[self.yax]

            xlen = xmax - xmin
            ylen = ymax - ymin

            xmin = xloc - oldxoff * xlen
            ymin = yloc - oldyoff * ylen

            xmax = xmin + xlen
            ymax = ymin + ylen

        log.debug('{}: Final display bounds: '
                  'X: ({: 5.1f}, {: 5.1f}) Y: ({: 5.1f}, {: 5.1f})'.format(
                      self.zax, xmin, xmax, ymin, ymax))

        self.displayBounds[:] = (xmin, xmax, ymin, ymax)


    def _setViewport(self, invertX=None, invertY=None):
        """Sets up the GL canvas size, viewport, and projection.

        :arg invertX: Invert the X axis. If not provided, taken from
                      :attr:`invertX`.

        :arg invertY: Invert the Y axis. If not provided, taken from
                      :attr:`invertY`.

        :returns: A sequence of three ``(low, high)`` values, defining the
                  display coordinate system bounding box. Note that this
                  sequence is ordered in absolute terms, not in terms of
                  the orientation of this ``SliceCanvas``.
        """

        xax  = self.xax
        yax  = self.yax
        zax  = self.zax
        xmin = self.displayBounds.xlo
        xmax = self.displayBounds.xhi
        ymin = self.displayBounds.ylo
        ymax = self.displayBounds.yhi
        zmin = self.displayCtx.bounds.getLo(zax)
        zmax = self.displayCtx.bounds.getHi(zax)
        size = self._getSize()

        if invertX is None: invertX = self.invertX
        if invertY is None: invertY = self.invertY

        width, height = size

        # If there are no images to be displayed,
        # or no space to draw, do nothing
        if (len(self.overlayList) == 0) or \
           (width  == 0)                or \
           (height == 0)                or \
           (xmin   == xmax)             or \
           (ymin   == ymax):
            return [(0, 0), (0, 0), (0, 0)]

        log.debug('Setting canvas bounds (size {}, {}): '
                  'X {: 5.1f} - {: 5.1f},'
                  'Y {: 5.1f} - {: 5.1f},'
                  'Z {: 5.1f} - {: 5.1f}'.format(
                      width, height, xmin, xmax, ymin, ymax, zmin, zmax))

        # Add a bit of padding to the depth limits
        zmin -= 1e-3
        zmax += 1e-3

        lo = [None] * 3
        hi = [None] * 3

        lo[xax], hi[xax] = xmin, xmax
        lo[yax], hi[yax] = ymin, ymax
        lo[zax], hi[zax] = zmin, zmax

        # set up 2D orthographic drawing
        glroutines.show2D(xax,
                          yax,
                          width,
                          height,
                          lo,
                          hi,
                          invertX,
                          invertY)

        return [(lo[0], hi[0]), (lo[1], hi[1]), (lo[2], hi[2])]


    def _drawCursor(self):
        """Draws a green cursor at the current X/Y position."""

        ovl        = self.displayCtx.getSelectedOverlay()
        xmin, xmax = self.displayCtx.bounds.getRange(self.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(self.yax)
        x          = self.pos.x
        y          = self.pos.y
        lines      = []

        # Just show a vertical line at xpos,
        # and a horizontal line at ypos
        if not self.cursorGap:
            lines.append(((x,    ymin), (x,    ymax)))
            lines.append(((xmin, y),    (xmax, y)))

        # Draw vertical/horizontal cursor lines,
        # with a gap at the cursor centre

        # Not a NIFTI image - just
        # use a fixed gap size
        elif ovl is None or not isinstance(ovl, fslimage.Nifti):

            lines.append(((xmin,    y),       (x - 0.5, y)))
            lines.append(((x + 0.5, y),       (xmax,    y)))
            lines.append(((x,       ymin),    (x,       y - 0.5)))
            lines.append(((x,       y + 0.5), (x,       ymax)))

        # If the current overlay is NIFTI, make
        # the gap size match its voxel size
        else:

            # Get the current voxel
            # coordinates,
            opts = self.displayCtx.getOpts(ovl)
            vox = opts.getVoxel(vround=False)

            # Out of bounds of the current
            # overlay, fall back to using
            # a fixed size gap
            if vox is None:
                xlow  = x - 0.5
                xhigh = x + 0.5
                ylow  = y - 0.5
                yhigh = y + 0.5
            else:

                vox  = np.array(vox, dtype=np.float32)

                # Figure out the voxel coord axes
                # that (approximately) correspond
                # with the display x/y axes.
                axes = ovl.axisMapping(opts.getTransform('voxel', 'display'))
                axes = np.abs(axes) - 1
                xax  = axes[self.xax]
                yax  = axes[self.yax]

                # Clamp the voxel x/y coords to
                # the voxel edge (round, then
                # offset by 0.5 - integer coords
                # correspond to the voxel centre).
                vox[xax] = np.round(vox[xax]) - 0.5
                vox[yax] = np.round(vox[yax]) - 0.5

                # Get the voxels that are above
                # and next to our current voxel.
                voxx = np.copy(vox)
                voxy = np.copy(vox)

                voxx[xax] += 1
                voxy[yax] += 1

                # Transform those integer coords back
                # into display coordinates to get the
                # display location on the voxel boundary.
                vloc  = opts.transformCoords(vox,  'voxel', 'display')
                vlocx = opts.transformCoords(voxx, 'voxel', 'display')
                vlocy = opts.transformCoords(voxy, 'voxel', 'display')

                xlow  = min(vloc[self.xax], vlocx[self.xax])
                xhigh = max(vloc[self.xax], vlocx[self.xax])
                ylow  = min(vloc[self.yax], vlocy[self.yax])
                yhigh = max(vloc[self.yax], vlocy[self.yax])

            lines.append(((xmin,  y),     (xlow, y)))
            lines.append(((xhigh, y),     (xmax, y)))
            lines.append(((x,     ymin),  (x,    ylow)))
            lines.append(((x,     yhigh), (x,    ymax)))

        kwargs = {
            'colour' : self.cursorColour,
            'width'  : 1
        }

        for line in lines:
            self._annotations.line(line[0], line[1], **kwargs)
            self._annotations.line(line[0], line[1], **kwargs)


    def _drawOffscreenTextures(self):
        """Draws all of the off-screen :class:`.GLObjectRenderTexture` instances to
        the canvas.

        This method is called by :meth:`_draw` if :attr:`renderMode` is
        set to ``offscreen``.
        """

        log.debug('Combining off-screen render textures, and rendering '
                  'to canvas (size {})'.format(self._getSize()))

        for overlay in self.displayCtx.getOrderedOverlays():

            rt      = self._offscreenTextures.get(overlay, None)
            display = self.displayCtx.getDisplay(overlay)
            opts    = display.getDisplayOpts()
            lo      = opts.bounds.getLo()
            hi      = opts.bounds.getHi()

            if rt is None or not display.enabled:
                continue

            xmin, xmax = lo[self.xax], hi[self.xax]
            ymin, ymax = lo[self.yax], hi[self.yax]

            log.debug('Drawing overlay {} texture to {:0.3f}-{:0.3f}, '
                      '{:0.3f}-{:0.3f}'.format(
                          overlay, xmin, xmax, ymin, ymax))

            rt.drawOnBounds(
                self.pos.z, xmin, xmax, ymin, ymax, self.xax, self.yax)


    def _draw(self, *a):
        """Draws the current scene to the canvas. """

        if self.destroyed():
            return

        width, height = self._getSize()
        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        overlays, globjs = self._getGLObjects()

        bbox = None

        # Set the viewport to match the current
        # display bounds and canvas size
        if self.renderMode is not 'offscreen':
            bbox = self._setViewport()
            glroutines.clear(self.bgColour)

        # Do not draw anything if some globjects
        # are not ready. This is because, if a
        # GLObject was drawn, but is now temporarily
        # not ready (e.g. it has an image texture
        # that is being asynchronously refreshed),
        # drawing the scene now would cause
        # flickering of that GLObject.
        if len(globjs) == 0 or any([not g.ready() for g in globjs]):
            return

        for overlay, globj in zip(overlays, globjs):

            display = self.displayCtx.getDisplay(overlay)
            opts    = display.getDisplayOpts()

            if not display.enabled:
                continue

            # On-screen rendering - the globject is
            # rendered directly to the screen canvas
            if self.renderMode == 'onscreen':
                log.debug('Drawing {} slice for overlay {} '
                          'directly to canvas'.format(
                              self.zax, display.name))

                globj.preDraw()
                globj.draw(self.pos.z, bbox=bbox)
                globj.postDraw()

            # Off-screen rendering - each overlay is
            # rendered to an off-screen texture -
            # these textures are combined below.
            # Set up the texture as the rendering
            # target, and draw to it
            elif self.renderMode == 'offscreen':

                rt = self._offscreenTextures.get(overlay, None)
                lo = opts.bounds.getLo()
                hi = opts.bounds.getHi()

                # Assume that all is well - the texture
                # just has not yet been created
                if rt is None:
                    log.debug('Render texture missing for overlay {}'.format(
                        overlay))
                    continue

                log.debug('Drawing {} slice for overlay {} '
                          'to off-screen texture'.format(
                              self.zax, overlay.name))

                rt.bindAsRenderTarget()
                rt.setRenderViewport(self.xax, self.yax, lo, hi)

                glroutines.clear((0, 0, 0, 0))

                with glroutines.disabled(gl.GL_BLEND):
                    globj.preDraw()
                    globj.draw(self.pos.z)
                    globj.postDraw()

                rt.unbindAsRenderTarget()
                rt.restoreViewport()

            # Pre-rendering - a pre-generated 2D
            # texture of the current z position
            # is rendered to the screen canvas
            elif self.renderMode == 'prerender':

                rt, name = self._prerenderTextures.get(overlay, (None, None))

                if rt is None:
                    continue

                log.debug('Drawing {} slice for overlay {} '
                          'from pre-rendered texture'.format(
                              self.zax, display.name))

                rt.draw(self.pos.z)

        # For off-screen rendering, all of the globjects
        # were rendered to off-screen textures - here,
        # those off-screen textures are all rendered on
        # to the screen canvas.
        if self.renderMode == 'offscreen':
            self._setViewport()
            glroutines.clear(self.bgColour)
            self._drawOffscreenTextures()

        if self.showCursor:
            self._drawCursor()

        self._annotations.draw(self.pos.z)
