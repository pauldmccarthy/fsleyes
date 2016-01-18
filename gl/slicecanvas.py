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

import numpy as np 

import props

import fsl.data.image                         as fslimage
import fsl.utils.async                        as async
import fsl.fsleyes.displaycontext             as fsldisplay
import fsl.fsleyes.displaycontext.canvasopts  as canvasopts
import fsl.fsleyes.gl.routines                as glroutines
import fsl.fsleyes.gl.resources               as glresources
import fsl.fsleyes.gl.globject                as globject
import fsl.fsleyes.gl.textures                as textures
import fsl.fsleyes.gl.annotations             as annotations


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

    
    The :attr:`renderMode` and :attr:`resolutionLimit` properties control
    various ``SliceCanvas`` performance settings, which can be useful when
    running in a low performance environment (e.g. when only a software based
    GL driver is available). See also the :attr:`.SceneOpts.performance`
    setting.

    
    The :attr:`resolutionLimit` property controls the highest resolution at
    which :class:`.Image` overlays are displayed on the ``SliceCanvas``. A
    higher value will result in faster rendering performance. When this
    property is changed, the :attr:`.Nifti1Opts.resolution` property for every
    :class:`.Image` overlay is updated.


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
    
       calcPixelDims
       canvasToWorld
       panDisplayBy
       centreDisplayAt
       panDisplayToShow
       getAnnotations
    """

    
    pos             = copy.copy(canvasopts.SliceCanvasOpts.pos)
    zoom            = copy.copy(canvasopts.SliceCanvasOpts.zoom)
    displayBounds   = copy.copy(canvasopts.SliceCanvasOpts.displayBounds)
    showCursor      = copy.copy(canvasopts.SliceCanvasOpts.showCursor)
    zax             = copy.copy(canvasopts.SliceCanvasOpts.zax)
    invertX         = copy.copy(canvasopts.SliceCanvasOpts.invertX)
    invertY         = copy.copy(canvasopts.SliceCanvasOpts.invertY)
    cursorColour    = copy.copy(canvasopts.SliceCanvasOpts.cursorColour)
    bgColour        = copy.copy(canvasopts.SliceCanvasOpts.bgColour)
    renderMode      = copy.copy(canvasopts.SliceCanvasOpts.renderMode)
    resolutionLimit = copy.copy(canvasopts.SliceCanvasOpts.resolutionLimit)
    
        
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
        # the overlay list
        self._offscreenTextures = {}
        self._prerenderTextures = {}

        # When the render mode is changed,
        # overlay resolutions are potentially
        # modified. When this happends, this
        # is used to store the old overlay
        # resolution, so it can be restored
        # if the render mode is changed back.
        # See the __resolutionLimitChanged
        # method.
        self.__overlayResolutions = {}

        # The zax property is the image axis which maps to the
        # 'depth' axis of this canvas. The _zAxisChanged method
        # also fixes the values of 'xax' and 'yax'.
        self.zax = zax
        self.xax = (zax + 1) % 3
        self.yax = (zax + 2) % 3

        self._annotations = annotations.Annotations(self.xax, self.yax)
        self._zAxisChanged() 

        # when any of the properties of this
        # canvas change, we need to redraw
        self.addListener('zax',           self.name, self._zAxisChanged)
        self.addListener('pos',           self.name, self._draw)
        self.addListener('displayBounds', self.name, self._draw)
        self.addListener('bgColour',      self.name, self._draw)
        self.addListener('cursorColour',  self.name, self._draw)
        self.addListener('showCursor',    self.name, self._draw)
        self.addListener('invertX',       self.name, self._draw)
        self.addListener('invertY',       self.name, self._draw)
        self.addListener('zoom',          self.name, self._zoomChanged)
        self.addListener('renderMode',    self.name, self._renderModeChange)
        self.addListener('resolutionLimit',
                         self.name,
                         self.__resolutionLimitChange) 
        
        # When the overlay list changes, refresh the
        # display, and update the display bounds
        self.overlayList.addListener('overlays',
                                     self.name,
                                     self._overlayListChanged)
        self.displayCtx .addListener('overlayOrder',
                                     self.name,
                                     self._refresh) 
        self.displayCtx .addListener('bounds',
                                     self.name,
                                     self._overlayBoundsChanged)
        self.displayCtx .addListener('syncOverlayDisplay',
                                     self.name,
                                     self._syncOverlayDisplayChanged) 


    def destroy(self):
        """This method must be called when this ``SliceCanvas`` is no longer
        being used.

        It removes listeners from all :class:`.OverlayList`,
        :class:`.DisplayContext`, and :class:`.Display` instances, and
        destroys OpenGL representations of all overlays.
        """
        self.removeListener('zax',           self.name)
        self.removeListener('pos',           self.name)
        self.removeListener('displayBounds', self.name)
        self.removeListener('showCursor',    self.name)
        self.removeListener('invertX',       self.name)
        self.removeListener('invertY',       self.name)
        self.removeListener('zoom',          self.name)
        self.removeListener('renderMode',    self.name)

        self.overlayList.removeListener('overlays',     self.name)
        self.displayCtx .removeListener('bounds',       self.name)
        self.displayCtx .removeListener('overlayOrder', self.name)

        for overlay in self.overlayList:
            disp  = self.displayCtx.getDisplay(overlay)
            globj = self._glObjects.get(overlay)

            disp.removeListener('overlayType',  self.name)
            disp.removeListener('enabled',      self.name)

            if globj is not None:
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


    def calcPixelDims(self):
        """Calculate and return the approximate size (width, height) of one
        pixel in display space.
        """
        
        xmin, xmax = self.displayCtx.bounds.getRange(self.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(self.yax)
        
        w, h = self._getSize()
        pixx = (xmax - xmin) / float(w)
        pixy = (ymax - ymin) / float(h) 

        return pixx, pixy

    
    def canvasToWorld(self, xpos, ypos):
        """Given pixel x/y coordinates on this canvas, translates them
        into xyz display coordinates.
        """

        realWidth                 = self.displayBounds.xlen
        realHeight                = self.displayBounds.ylen
        canvasWidth, canvasHeight = map(float, self._getSize())
            
        if self.invertX: xpos = canvasWidth  - xpos
        if self.invertY: ypos = canvasHeight - ypos

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
        
        dispBounds = self.displayBounds
        ovlBounds  = self.displayCtx.bounds

        xmin, xmax, ymin, ymax = self.displayBounds[:]

        xmin = xmin + xoff
        xmax = xmax + xoff
        ymin = ymin + yoff
        ymax = ymax + yoff

        if dispBounds.xlen > ovlBounds.getLen(self.xax):
            xmin = dispBounds.xlo
            xmax = dispBounds.xhi
            
        elif xmin < ovlBounds.getLo(self.xax):
            xmin = ovlBounds.getLo(self.xax)
            xmax = xmin + self.displayBounds.getLen(0)
            
        elif xmax > ovlBounds.getHi(self.xax):
            xmax = ovlBounds.getHi(self.xax)
            xmin = xmax - self.displayBounds.getLen(0)
            
        if dispBounds.ylen > ovlBounds.getLen(self.yax):
            ymin = dispBounds.ylo
            ymax = dispBounds.yhi
            
        elif ymin < ovlBounds.getLo(self.yax):
            ymin = ovlBounds.getLo(self.yax)
            ymax = ymin + self.displayBounds.getLen(1)

        elif ymax > ovlBounds.getHi(self.yax):
            ymax = ovlBounds.getHi(self.yax)
            ymin = ymax - self.displayBounds.getLen(1)

        self.displayBounds[:] = [xmin, xmax, ymin, ymax]


    def centreDisplayAt(self, xpos, ypos):
        """Pans the display so the given x/y position is in the centre. """

        # work out current display centre
        bounds  = self.displayBounds
        xcentre = bounds.xlo + (bounds.xhi - bounds.xlo) * 0.5
        ycentre = bounds.ylo + (bounds.yhi - bounds.ylo) * 0.5

        # move to the new centre
        self.panDisplayBy(xpos - xcentre, ypos - ycentre)


    def panDisplayToShow(self, xpos, ypos):
        """Pans the display so that the given x/y position (in display
        coordinates) is visible.
        """

        bounds = self.displayBounds

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


    def getAnnotations(self):
        """Returns an :class:`.Annotations` instance, which can be used to
        annotate the canvas.
        """
        return self._annotations
            

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
            for ovl, texture in self._offscreenTextures.items():
                if ovl not in self.overlayList:
                    self._offscreenTextures.pop(ovl)
                    texture.destroy()
            
        elif self.renderMode == 'prerender':
            for ovl, (texture, name) in self._prerenderTextures.items():
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

            if globj is None:
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

        self._refresh()

        
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
        for ovl, texture in self._offscreenTextures.items():
            self._offscreenTextures.pop(ovl)
            texture.destroy()
            
        for ovl, (texture, name) in self._prerenderTextures.items():
            self._prerenderTextures.pop(ovl)
            glresources.delete(name)

        # Onscreen rendering - each GLObject
        # is rendered directly to the canvas
        # displayed on the screen, so render
        # textures are not needed.
        if self.renderMode == 'onscreen':
            self._refresh()
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
    

    def __resolutionLimitChange(self, *a):
        """Called when the :attr:`resolutionLimit` property changes.

        Updates the :attr:`.Nifti1Opts.resolution` of all :class:`.Nifti1`
        overlays in the overlay list.  Whenever the resolution of an
        overlay is changed, its old value is saved, so it can be restored
        later on when possible.
        """

        limit = self.resolutionLimit

        for ovl in self.overlayList:

            opts = self.displayCtx.getOpts(ovl)

            # No support for non-volumetric overlay 
            # types yet (or maybe ever?)
            if not isinstance(opts, fsldisplay.Nifti1Opts):
                continue
            
            currRes = opts.resolution
            lastRes = self.__overlayResolutions.get(ovl)

            listening = opts.hasListener('resolution', self.name)

            if listening:
                opts.disableListener('resolution', self.name)

            # The overlay resolution is below
            # the limit - set it to the limit
            if currRes < limit:

                log.debug('Limiting overlay {} resolution to {}'.format(
                    ovl, limit))

                opts.resolution = limit

                # Save the old resolution so we
                # can restore it later if needed
                if ovl not in self.__overlayResolutions:
                    log.debug('Caching overlay {} resolution: {}'.format(
                        ovl, limit))
                    
                    self.__overlayResolutions[ovl] = currRes

            # We have previously modified the
            # resolution of this overlay - restore
            # it
            elif ovl in self.__overlayResolutions:

                # but only if the old resolution
                # is within the new limits. 
                if lastRes >= limit:

                    log.debug('Restoring overlay {} resolution to {}, '
                              'and clearing cache'.format(ovl, lastRes))
                    opts.resolution = lastRes

                    # We've restored the modified overlay
                    # resolution - clear it from the cache
                    self.__overlayResolutions.pop(ovl)
                else:
                    log.debug('Limiting overlay {} resolution to {}'.format(
                        ovl, limit))
                    opts.resolution = limit

            if listening:
                opts.enableListener('resolution', self.name)
                        

    def __overlayResolutionChanged(self, value, valid, opts, name):
        """Called when the :attr:`.Nifti1Opts.resolution` property for any
        :class:`.Image` overlay changes. Clears the saved resolution for
        the overlay if necessary (see :meth:`__resolutionLimitChange`).
        """
        self.__overlayResolutions.pop(opts.overlay, None)


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
        dims = range(3)
        dims.pop(self.zax)
        self.xax = dims[0]
        self.yax = dims[1]

        self._annotations.setAxes(self.xax, self.yax)

        for ovl, globj in self._glObjects.items():

            if globj is not None:
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

        self.__genGLObject(display.getOverlay())
        self._refresh()


    def __genGLObject(self, overlay, updateRenderTextures=True, refresh=True):
        """Creates a :class:`.GLObject` instance for the given ``overlay``,
        destroying any existing instance.

        If ``updateRenderTextures`` is ``True`` (the default), and the
        :attr:`.renderMode` is ``offscreen`` or ``prerender``, any
        render texture associated with the overlay is destroyed.

        If ``refresh`` is ``True`` (the default), the :meth:`_refresh` method
        is called after the ``GLObject`` has been created.

        .. note:: If running in ``wx`` (i.e. via a :class:`.WXGLSliceCanvas`),
                  the :class:`.GLObject` instnace will be created on the
                  ``wx.EVT_IDLE`` lopp (via the :mod:`.idle` module).
        """

        display = self.displayCtx.getDisplay(overlay)

        # Tell the previous GLObject (if
        # any) to clean up after itself
        globj = self._glObjects.pop(overlay, None)
        if globj is not None:
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

        def create():

            # We need a GL context to create a new GL
            # object. If we can't get it now, we simply
            # reschedule this function to be run later
            # on.
            if not self._setGLContext():
                async.idle(create)
                return

            globj = globject.createGLObject(overlay, display)

            if globj is not None:
                globj.setAxes(self.xax, self.yax)
                globj.register(self.name, self._refresh)

            self._glObjects[overlay] = globj

            if updateRenderTextures:
                self._updateRenderTextures() 

            display.addListener('overlayType',
                                self.name,
                                self.__overlayTypeChanged,
                                overwrite=True)

            display.addListener('enabled',
                                self.name,
                                self._refresh,
                                overwrite=True)

            # Listen for resolution changes on Image
            # overlays - see __overlayResolutionChanged,
            # and __resolutionLimitChanged
            if isinstance(overlay, fslimage.Nifti1): 
                opts = display.getDisplayOpts()
                opts.addListener('resolution',
                                 self.name,
                                 self.__overlayResolutionChanged,
                                 overwrite=True)

            if refresh:
                self._refresh()

        async.idle(create)

        
    def _overlayListChanged(self, *args, **kwargs):
        """This method is called every time an overlay is added or removed
        to/from the overlay list.

        For newly added overlays, calls the :meth:`__genGLObject` method,
        which initialises the OpenGL data necessary to render the
        overlay.
        """

        # Destroy any GL objects for overlays
        # which are no longer in the list
        for ovl, globj in self._glObjects.items():
            if ovl not in self.overlayList:
                self._glObjects.pop(ovl)
                if globj is not None:
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

            self.__genGLObject(overlay,
                               updateRenderTextures=False,
                               refresh=False)

        # All the GLObjects are created using
        # async.idle, so we call refresh in the
        # same way to make sure it gets called
        # after all the GLObject creations.
        def refresh():
            self._updateRenderTextures()
            self.__resolutionLimitChange()
            self._refresh()

        async.idle(refresh)


    def _overlayBoundsChanged(self, *a):
        """Called when the display bounds are changed.

        Updates the constraints on the :attr:`pos` property so it is
        limited to stay within a valid range, and then calls the
        :meth:`_updateDisplayBounds` method.
        """

        ovlBounds = self.displayCtx.bounds
        oldPos    = self.pos.xy

        self.disableNotification('pos')
        self.pos.setMin(0, ovlBounds.getLo(self.xax))
        self.pos.setMax(0, ovlBounds.getHi(self.xax))
        self.pos.setMin(1, ovlBounds.getLo(self.yax))
        self.pos.setMax(1, ovlBounds.getHi(self.yax))
        self.pos.setMin(2, ovlBounds.getLo(self.zax))
        self.pos.setMax(2, ovlBounds.getHi(self.zax))
        self.enableNotification('pos')

        self._updateDisplayBounds(oldLoc=oldPos)


    def _zoomChanged(self, *a):
        """Called when the :attr:`zoom` property changes. Updates the
        display bounds.
        """
        self._updateDisplayBounds()
        

    def _applyZoom(self, xmin, xmax, ymin, ymax):
        """*Zooms* in to the given rectangle according to the
        current value of the zoom property, keeping the view
        centre consistent with respect to the current value
        of the :attr:`displayBounds` property. Returns a
        4-tuple containing the updated bound values.
        """

        if self.zoom == 100.0:
            return (xmin, xmax, ymin, ymax)

        bounds     = self.displayBounds
        zoomFactor = 100.0 / self.zoom

        xlen    = xmax - xmin
        ylen    = ymax - ymin
        newxlen = xlen * zoomFactor
        newylen = ylen * zoomFactor
 
        # centre the zoomed-in rectangle on
        # the current displayBounds centre
        xmid = bounds.xlo + 0.5 * bounds.xlen
        ymid = bounds.ylo + 0.5 * bounds.ylen

        # new x/y min/max bounds
        xmin = xmid - 0.5 * newxlen
        xmax = xmid + 0.5 * newxlen
        ymin = ymid - 0.5 * newylen
        ymax = ymid + 0.5 * newylen

        xlen = xmax - xmin
        ylen = ymax - ymin

        # clamp x/y min/max values to the
        # displayBounds constraints
        if xmin < bounds.getMin(0):
            xmin = bounds.getMin(0)
            xmax = xmin + xlen
            
        elif xmax > bounds.getMax(0):
            xmax = bounds.getMax(0)
            xmin = xmax - xlen
            
        if ymin < bounds.getMin(1):
            ymin = bounds.getMin(1)
            ymax = ymin + ylen

        elif ymax > bounds.getMax(1):
            ymax = bounds.getMax(1)
            ymin = ymax - ylen

        return (xmin, xmax, ymin, ymax)

        
    def _updateDisplayBounds(self,
                             xmin=None,
                             xmax=None,
                             ymin=None,
                             ymax=None,
                             oldLoc=None):
        """Called on canvas resizes, overlay bound changes, and zoom changes.
        
        Calculates the bounding box, in display coordinates, to be displayed on
        the canvas. Stores this bounding box in the displayBounds property. If
        any of the parameters are not provided, the
        :attr:`.DisplayContext.bounds` are used.

        
        .. note:: This method is used internally, and also by the
                  :class:`.WXGLSliceCanvas` class.

        .. warning:: This code assumes that, if the display coordinate system
                     has changed, the display context location has already
                     been updated.  See the
                     :meth:`.DisplayContext.__displaySpaceChanged` method.
        
        
        :arg xmin:   Minimum x (horizontal) value to be in the display bounds.
        :arg xmax:   Maximum x value to be in the display bounds.
        :arg ymin:   Minimum y (vertical) value to be in the display bounds.
        :arg ymax:   Maximum y value to be in the display bounds.
        :arg oldLoc: If provided, should be the ``(x, y)`` location shown on
                     this ``SliceCanvas`` - the new display bounds will be
                     adjusted so that this location remains the same, with
                     respect to the new field of view.
        """

        if xmin is None: xmin = self.displayCtx.bounds.getLo(self.xax)
        if xmax is None: xmax = self.displayCtx.bounds.getHi(self.xax)
        if ymin is None: ymin = self.displayCtx.bounds.getLo(self.yax)
        if ymax is None: ymax = self.displayCtx.bounds.getHi(self.yax)

        log.debug('Required display bounds: X: ({}, {}) Y: ({}, {})'.format(
            xmin, xmax, ymin, ymax))

        canvasWidth, canvasHeight = self._getSize()
        dispWidth                 = float(xmax - xmin)
        dispHeight                = float(ymax - ymin)

        if canvasWidth  == 0 or \
           canvasHeight == 0 or \
           dispWidth    == 0 or \
           dispHeight   == 0:
            self.displayBounds[:] = [xmin, xmax, ymin, ymax]
            return

        # These ratios are used to determine whether
        # we need to expand the display range to
        # preserve the image aspect ratio.
        dispRatio   =       dispWidth    / dispHeight
        canvasRatio = float(canvasWidth) / canvasHeight

        # the canvas is too wide - we need
        # to expand the display width, thus 
        # effectively shrinking the display
        # along the horizontal axis
        if canvasRatio > dispRatio:
            newDispWidth = canvasWidth * (dispHeight / canvasHeight)
            xmin         = xmin - 0.5 * (newDispWidth - dispWidth)
            xmax         = xmax + 0.5 * (newDispWidth - dispWidth)

        # the canvas is too high - we need
        # to expand the display height
        elif canvasRatio < dispRatio:
            newDispHeight = canvasHeight * (dispWidth / canvasWidth)
            ymin          = ymin - 0.5 * (newDispHeight - dispHeight)
            ymax          = ymax + 0.5 * (newDispHeight - dispHeight)

        oldxmin, oldxmax, oldymin, oldymax = self.displayBounds[:]

        self.disableNotification('displayBounds')
        self.displayBounds.setLimits(0, xmin, xmax)
        self.displayBounds.setLimits(1, ymin, ymax)
        self.enableNotification('displayBounds')

        xmin, xmax, ymin, ymax = self._applyZoom(xmin, xmax, ymin, ymax)

        if oldLoc and (oldxmax > oldxmin) and (oldymax > oldymin):

            # Calculate the normalised distance from the
            # old cursor loaction to the old bound corner
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
            
        log.debug('Final display bounds: X: ({}, {}) Y: ({}, {})'.format(
            xmin, xmax, ymin, ymax))

        self.displayBounds[:] = (xmin, xmax, ymin, ymax)

        
    def _setViewport(self,
                     xmin=None,
                     xmax=None,
                     ymin=None,
                     ymax=None,
                     zmin=None,
                     zmax=None,
                     size=None):
        """Sets up the GL canvas size, viewport, and projection.

        
        If any of the min/max parameters are not provided, they are
        taken from the :attr:`displayBounds` (x/y), and the 
        :attr:`DisplayContext.bounds` (z).

        
        :arg xmin: Minimum x (horizontal) location
        :arg xmax: Maximum x location
        :arg ymin: Minimum y (vertical) location
        :arg ymax: Maximum y location
        :arg zmin: Minimum z (depth) location
        :arg zmax: Maximum z location
        """

        xax = self.xax
        yax = self.yax
        zax = self.zax
        
        if xmin is None: xmin = self.displayBounds.xlo
        if xmax is None: xmax = self.displayBounds.xhi
        if ymin is None: ymin = self.displayBounds.ylo
        if ymax is None: ymax = self.displayBounds.yhi
        if zmin is None: zmin = self.displayCtx.bounds.getLo(zax)
        if zmax is None: zmax = self.displayCtx.bounds.getHi(zax)

        # If there are no images to be displayed,
        # or no space to draw, do nothing
        if size is None:
            size = self._getSize()
            
        width, height = size
        
        if (len(self.overlayList) == 0) or \
           (width  == 0)                or \
           (height == 0)                or \
           (xmin   == xmax)             or \
           (ymin   == ymax):
            return

        log.debug('Setting canvas bounds (size {}, {}): '
                  'X {: 5.1f} - {: 5.1f},'
                  'Y {: 5.1f} - {: 5.1f},'
                  'Z {: 5.1f} - {: 5.1f}'.format(
                      width, height, xmin, xmax, ymin, ymax, zmin, zmax))

        # Flip the viewport if necessary
        if self.invertX: xmin, xmax = xmax, xmin
        if self.invertY: ymin, ymax = ymax, ymin

        lo = [None] * 3
        hi = [None] * 3

        lo[xax], hi[xax] = xmin, xmax
        lo[yax], hi[yax] = ymin, ymax
        lo[zax], hi[zax] = zmin, zmax

        # set up 2D orthographic drawing
        glroutines.show2D(xax, yax, width, height, lo, hi)

        
    def _drawCursor(self):
        """Draws a green cursor at the current X/Y position."""
        
        # A vertical line at xpos, and a horizontal line at ypos
        xverts = np.zeros((2, 2))
        yverts = np.zeros((2, 2))

        xmin, xmax = self.displayCtx.bounds.getRange(self.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(self.yax)

        x = self.pos.x
        y = self.pos.y

        # How big is one pixel in world space?
        pixx, pixy = self.calcPixelDims()

        # add a little padding to the lines if they are 
        # on the boundary, so they don't get cropped        
        if x <= xmin: x = xmin + 0.5 * pixx
        if x >= xmax: x = xmax - 0.5 * pixx
        if y <= ymin: y = ymin + 0.5 * pixy
        if y >= ymax: y = ymax - 0.5 * pixy

        xverts[:, 0] = x
        xverts[:, 1] = [ymin, ymax]
        yverts[:, 0] = [xmin, xmax]
        yverts[:, 1] = y

        kwargs = {
            'colour' : self.cursorColour,
            'width'  : 1
        }
        
        self._annotations.line(xverts[0], xverts[1], **kwargs)
        self._annotations.line(yverts[0], yverts[1], **kwargs)


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
        
        width, height = self._getSize()
        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        # Set the viewport to match the current 
        # display bounds and canvas size
        if self.renderMode is not 'offscreen':
            self._setViewport()
            glroutines.clear(self.bgColour)
            
        for overlay in self.displayCtx.getOrderedOverlays():

            display = self.displayCtx.getDisplay(overlay)
            opts    = display.getDisplayOpts()
            globj   = self._glObjects.get(overlay, None)

            if not display.enabled:
                continue
            
            if globj is None:
                # The GLObject has not been created
                # yet - we assume here that the
                # __genGLObject method is on the case
                continue

            # The GLObject is not ready
            # to be drawn yet.
            if not globj.ready():
                continue

            # On-screen rendering - the globject is
            # rendered directly to the screen canvas
            if self.renderMode == 'onscreen':
                log.debug('Drawing {} slice for overlay {} '
                          'directly to canvas'.format(
                              self.zax, display.name))

                globj.preDraw()
                globj.draw(self.pos.z)
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

        self._postDraw()
