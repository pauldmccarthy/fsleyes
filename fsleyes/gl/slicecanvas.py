#!/usr/bin/env python
#
# slicecanvas.py - The SliceCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SliceCanvas` class, which contains the
functionality to display a 2D slice from a collection of 3D overlays.
"""


import logging

import OpenGL.GL as gl

import numpy as np

import fsl.data.image                     as fslimage
import fsl.utils.idle                     as idle
import fsl.transform.affine               as affine
import fsleyes_widgets.utils.status       as status
import fsleyes_props                      as props

import fsleyes.strings                    as strings
import fsleyes.displaycontext.canvasopts  as canvasopts
import fsleyes.gl.routines                as glroutines
import fsleyes.gl.resources               as glresources
import fsleyes.gl.globject                as globject
import fsleyes.gl.annotations             as annotations


log = logging.getLogger(__name__)


class SliceCanvas:
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


    The ``SliceCanvas`` creates a :class:`.SliceCanvasOpts` instance to manage
    its settings. The scene scene displayed on a ``SliceCanvas`` instance can
    be manipulated via the properties of its ``SliceCanvasOpts`` instnace,
    which is accessed via the ``opts`` attribute.


    **GL objects**


    The ``SliceCanvas`` draws :class:`.GLObject` instances. When created, a
    ``SliceCanvas`` creates a :class:`.GLObject` instance for every overlay in
    the :class:`.OverlayList`. When an overlay is added or removed, it
    creates/destroys ``GLObject`` instances accordingly.  Furthermore,
    whenever the :attr:`.Display.overlayType` for an existing overlay
    changes, the ``SliceCanvas`` destroys the old ``GLObject`` associated with
    the overlay, and creates a new one.


    ``GLObject`` instances may be shared amongst multiple ``SliceCanvas``
    instances - this is achieved with the :mod:`.resources` module.


    The ``SliceCanvas`` also uses an :class:`.Annotations` instance, for
    drawing simple annotations on top of the overlays.  This ``Annotations``
    instance can be accessed with the :meth:`getAnnotations` method.


    **Attributes and methods**


    The following attributes are available on a ``SliceCanvas``:


    =============== ===========================================
    ``name``        A unique name for this ``SliceCanvas``
    ``opts``        Reference to the :class:`.SliceCanvasOpts`.
    ``overlayList`` Reference to the :class:`.OverlayList`.
    ``displayCtx``  Reference to the :class:`.DisplayContext`.
    =============== ===========================================


    The following convenience methods are available on a ``SliceCanvas``:

    .. autosummary::
       :nosignatures:

       canvasToWorld
       worldToCanvas
       pixelSize
       panDisplayBy
       centreDisplayAt
       panDisplayToShow
       zoomTo
       resetDisplay
       getAnnotations
       viewport
       projectionMatrix
       viewMatrix
    """


    def __init__(self, overlayList, displayCtx, zax=0, opts=None):
        """Create a ``SliceCanvas``.

        :arg overlayList: An :class:`.OverlayList` object containing a
                          collection of overlays to be displayed.

        :arg displayCtx:  A :class:`.DisplayContext` object which describes
                          how the overlays should be displayed.

        :arg zax:         Display coordinate system axis perpendicular to the
                          plane to be displayed (the *depth* axis), default 0.
        """

        if opts is None:
            opts = canvasopts.SliceCanvasOpts()

        self.opts        = opts
        self.overlayList = overlayList
        self.displayCtx  = displayCtx
        self.name        = '{}_{}'.format(self.__class__.__name__, id(self))

        # A GLObject instance is created for
        # every overlay in the overlay list,
        # and stored in this dictionary
        self._glObjects = {}

        # Copies of the final viewport, modelView and
        # projection matrices are stored here on each
        # call to _draw.  They can be accessed via the
        # viewport, projectionMatrix, and viewMatrix
        # methods.
        self.__viewport         = None
        self.__projectionMatrix = None
        self.__viewMatrix       = None

        # The zax property is the image axis which
        # maps to the 'depth' axis of this canvas.
        opts.zax = zax

        # when any of the properties of this
        # canvas change, we need to redraw
        opts.addListener('zax',           self.name, self._zAxisChanged)
        opts.addListener('pos',           self.name, self.Refresh)
        opts.addListener('displayBounds', self.name, self.Refresh)
        opts.addListener('bgColour',      self.name, self.Refresh)
        opts.addListener('cursorColour',  self.name, self.Refresh)
        opts.addListener('cursorWidth',   self.name, self.Refresh)
        opts.addListener('showCursor',    self.name, self.Refresh)
        opts.addListener('cursorGap',     self.name, self.Refresh)
        opts.addListener('invertX',       self.name, self.Refresh)
        opts.addListener('invertY',       self.name, self.Refresh)
        opts.addListener('zoom',          self.name, self._zoomChanged)
        opts.addListener('highDpi',       self.name, self._highDpiChange)

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
        self.displayCtx .addListener('displaySpace',
                                     self.name,
                                     self._displaySpaceChanged)

        # The zAxisChanged method
        # will kick everything off
        self._annotations = annotations.Annotations(self)
        self._zAxisChanged()


    def destroy(self):
        """This method must be called when this ``SliceCanvas`` is no longer
        being used.

        It removes listeners from all :class:`.OverlayList`,
        :class:`.DisplayContext`, and :class:`.Display` instances, and
        destroys OpenGL representations of all overlays.
        """
        opts = self.opts
        opts.removeListener('zax',             self.name)
        opts.removeListener('pos',             self.name)
        opts.removeListener('displayBounds',   self.name)
        opts.removeListener('showCursor',      self.name)
        opts.removeListener('invertX',         self.name)
        opts.removeListener('invertY',         self.name)
        opts.removeListener('zoom',            self.name)
        opts.removeListener('highDpi',         self.name)

        self.overlayList.removeListener('overlays',     self.name)
        self.displayCtx .removeListener('bounds',       self.name)
        self.displayCtx .removeListener('displaySpace', self.name)
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
                glresources.delete(self.globjectId(overlay))

        self._annotations.destroy()

        self._annotations = None
        self.opts         = None
        self.overlayList  = None
        self.displayCtx   = None
        self._glObjects   = None


    @property
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

        opts = self.opts

        if invertX is None: invertX = opts.invertX
        if invertY is None: invertY = opts.invertY

        realWidth                 = opts.displayBounds.xlen
        realHeight                = opts.displayBounds.ylen
        canvasWidth, canvasHeight = [float(s) for s in self.GetSize()]

        if invertX: xpos = canvasWidth  - xpos
        if invertY: ypos = canvasHeight - ypos

        if realWidth    == 0 or \
           canvasWidth  == 0 or \
           realHeight   == 0 or \
           canvasHeight == 0:
            return None

        xpos = opts.displayBounds.xlo + (xpos / canvasWidth)  * realWidth
        ypos = opts.displayBounds.ylo + (ypos / canvasHeight) * realHeight

        pos = [None] * 3
        pos[opts.xax] = xpos
        pos[opts.yax] = ypos
        pos[opts.zax] = opts.pos[opts.zax]

        return pos


    def worldToCanvas(self, pos):
        """Converts a location in the display coordinate system into
        an x/y location in pixels relative to this ``SliceCanvas``.
        """

        opts    = self.opts
        xpos    = pos[opts.xax]
        ypos    = pos[opts.yax]
        invertX = opts.invertX
        invertY = opts.invertY

        xmin          = opts.displayBounds.xlo
        xlen          = opts.displayBounds.xlen
        ymin          = opts.displayBounds.ylo
        ylen          = opts.displayBounds.ylen
        width, height = [float(s) for s in self.GetSize()]

        if xlen   == 0 or \
           ylen   == 0 or \
           width  == 0 or \
           height == 0:
            return None

        xpos = width  * ((xpos - xmin) / xlen)
        ypos = height * ((ypos - ymin) / ylen)

        if invertX: xpos = width  - xpos
        if invertY: ypos = height - ypos

        return xpos, ypos


    def pixelSize(self):
        """Returns the current (x, y) size of one logical pixel in display
        coordinates.
        """
        w, h = self.GetSize()
        xlen = self.opts.displayBounds.xlen
        ylen = self.opts.displayBounds.ylen
        return (xlen / w, ylen / h)


    def panDisplayBy(self, xoff, yoff):
        """Pans the canvas display by the given x/y offsets (specified in
        display coordinates).
        """

        if len(self.overlayList) == 0: return

        xmin, xmax, ymin, ymax = self.opts.displayBounds[:]

        xmin = xmin + xoff
        xmax = xmax + xoff
        ymin = ymin + yoff
        ymax = ymax + yoff

        self.opts.displayBounds[:] = [xmin, xmax, ymin, ymax]


    def centreDisplayAt(self, xpos, ypos):
        """Pans the display so the given x/y position is in the centre. """

        xcentre, ycentre = self.getDisplayCentre()
        self.panDisplayBy(xpos - xcentre, ypos - ycentre)


    def getDisplayCentre(self):
        """Returns the horizontal/vertical position, in display coordinates,
        of the current centre of the display bounds.
        """
        bounds  = self.opts.displayBounds
        xcentre = bounds.xlo + (bounds.xhi - bounds.xlo) * 0.5
        ycentre = bounds.ylo + (bounds.yhi - bounds.ylo) * 0.5

        return xcentre, ycentre


    def panDisplayToShow(self, xpos, ypos):
        """Pans the display so that the given x/y position (in display
        coordinates) is visible.
        """

        bounds = self.opts.displayBounds

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
        opts       = self.opts
        xmin, xmax = self.displayCtx.bounds.getRange(opts.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(opts.yax)
        zoommin    = opts.getAttribute('zoom', 'minval')
        zoommax    = opts.getAttribute('zoom', 'maxval')

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
        with props.skip(opts, 'zoom',          self.name), \
             props.skip(opts, 'displayBounds', self.name):
            opts.zoom = zoom
            self._updateDisplayBounds()
            self.centreDisplayAt(xmid, ymid)

        self.Refresh()


    def resetDisplay(self):
        """Resets the :attr:`zoom` to 100%, and sets the canvas display
        bounds to the overaly bounding box (from the
        :attr:`.DisplayContext.bounds`)
        """

        opts = self.opts

        with props.skip(opts, 'zoom', self.name):
            opts.zoom = 100

        with props.suppress(opts, 'displayBounds'):
            self._updateDisplayBounds()

        self.Refresh()


    def getAnnotations(self):
        """Returns an :class:`.Annotations` instance, which can be used to
        annotate the canvas.
        """
        return self._annotations


    def globjectId(self, overlay):
        """Returns a key that can be used to uniquely identify a
        :class:`.GLObject` for the given overlay. ``GLObject`` instances may be
        shared between different ``SliceCanvas`` instances (specifically, the
        three canvases of an :class:`.OrthoPanel`) using the :mod:`.resources`
        module, using this key.
        """
        return ('GLObject', id(self.displayCtx), overlay)


    def getGLObject(self, overlay):
        """Returns the :class:`.GLObject` associated with the given
        ``overlay``, or ``None`` if there isn't one.
        """
        globj = self._glObjects.get(overlay, None)

        # globjs can be set to False
        if not globj: return None
        else:         return globj


    @property
    def viewport(self):
        """Return the current viewport, as  a sequence of three ``(low, high)``
        values, defining the bounding box in the display coordinate system.

        This method will return ``None`` if :meth:`_draw` has not yet been
        called.
        """
        return self.__viewport


    @property
    def viewMatrix(self):
        """Returns the current model view matrix. """
        return self.__viewMatrix


    @property
    def projectionMatrix(self):
        """Returns the current projection matrix. """
        return self.__projectionMatrix


    @property
    def mvpMatrix(self):
        """Returns the current model*view*projection matrix. """
        return affine.concat(self.__projectionMatrix, self.__viewMatrix)


    def _initGL(self):
        """Call the :meth:`_overlayListChanged` method - it will generate
        any necessary GL data for each of the overlays.
        """
        self._overlayListChanged()


    def _highDpiChange(self, *a):
        """Called when the :attr:`.SliceCanvasOpts.highDpi` property
        changes. Calls the :meth:`.GLCanvasTarget.EnableHighDPI` method.
        """
        self.EnableHighDPI(self.opts.highDpi)


    def _zAxisChanged(self, *a):
        """Called when the :attr:`zax` property is changed. Notifies
        the :class:`.Annotations` instance, and calls :meth:`resetDisplay`.
        """

        opts = self.opts

        log.debug('{}'.format(opts.zax))
        self.resetDisplay()


    def __overlayTypeChanged(self, value, valid, display, name):
        """Called when the :attr:`.Display.overlayType` setting for any
        overlay changes. Makes sure that an appropriate :class:`.GLObject`
        has been created for the overlay (see the :meth:`__genGLObject`
        method).
        """

        log.debug('GLObject representation for {} '
                  'changed to {}'.format(display.name,
                                         display.overlayType))

        self.__regenGLObject(display.overlay)
        self.Refresh()


    def __regenGLObject(self, overlay, refresh=True):
        """Destroys any existing :class:`.GLObject` associated with the given
        ``overlay``, and creates a new one (via the :meth:`__genGLObject`
        method).
        """

        # Tell the previous GLObject (if
        # any) to clean up after itself

        globj = self._glObjects.pop(overlay, None)
        if globj:
            globj.deregister(self.name)
            glresources.delete(self.globjectId(overlay))

        self.__genGLObject(overlay, refresh)


    def __genGLObject(self, overlay, refresh=True):
        """Creates a :class:`.GLObject` instance for the given ``overlay``.
        Does nothing if a ``GLObject`` already exists for the given overlay.

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

            if not self or self.destroyed:
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

            globj = glresources.get(self.globjectId(overlay),
                                    globject.createGLObject,
                                    overlay,
                                    self.overlayList,
                                    self.displayCtx,
                                    False)

            if globj is not None:
                globj.register(self.name, self.__onGLObjectUpdate)

            self._glObjects[overlay] = globj

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

        idle.idle(create)


    def __onGLObjectUpdate(self, globj, *a):
        """Called when a :class:`.GLObject` has been updated, and needs to be
        redrawn.
        """

        # we can sometimes get called after
        # being destroyed (e.g. during testing)
        if self.destroyed:
            return
        self.Refresh()


    def _overlayListChanged(self, *args, **kwargs):
        """This method is called every time an overlay is added or removed
        to/from the overlay list.

        For newly added overlays, calls the :meth:`__genGLObject` method,
        which initialises the OpenGL data necessary to render the
        overlay.
        """

        if self.destroyed:
            return

        # Destroy any GL objects for overlays
        # which are no longer in the list
        for ovl, globj in list(self._glObjects.items()):
            if ovl not in self.overlayList:
                self._glObjects.pop(ovl)
                if globj:
                    glresources.delete(self.globjectId(ovl))

        # Create a GL object for any new overlays,
        # and attach a listener to their display
        # properties so we know when to refresh
        # the canvas.
        for overlay in self.overlayList:

            # A GLObject already exists
            # for this overlay
            if overlay in self._glObjects:
                continue

            self.__regenGLObject(overlay, refresh=False)

        # All the GLObjects are created using
        # idle.idle, so we call refresh in the
        # same way to make sure it gets called
        # after all the GLObject creations.
        def refresh():

            # This SliceCanvas might get
            # destroyed before this idle
            # task is executed
            if not self or self.destroyed:
                return

            self.Refresh()

        idle.idle(refresh)


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
            if globj is None:
                self.__genGLObject(ovl)

            # If there is a value for this overlay in
            # the globjects dictionary, but it evaluates
            # to False, then GLObject creation has been
            # scheduled for the overlay - see genGLObject.
            elif globj:
                overlays.append(ovl)
                globjs  .append(globj)

        return overlays, globjs


    def _overlayBoundsChanged(self, *args, **kwargs):
        """Called when the :attr:`.DisplayContext.bounds` are changed.
        Initialises/resets the display bounds, and/or preserves the zoom
        level if necessary.

        :arg preserveZoom: Must be passed as a keyword argument. If ``True``
                           (the default), the :attr:`zoom` value is adjusted
                           so that the effective zoom is preserved
        """

        preserveZoom = kwargs.get('preserveZoom', True)

        opts = self.opts
        xax  = opts.xax
        yax  = opts.yax
        xmin = self.displayCtx.bounds.getLo(xax)
        xmax = self.displayCtx.bounds.getHi(xax)
        ymin = self.displayCtx.bounds.getLo(yax)
        ymax = self.displayCtx.bounds.getHi(yax)
        width, height = self.GetSize()

        if np.isclose(xmin, xmax) or width == 0 or height == 0:
            return

        if not preserveZoom or opts.displayBounds.xlen == 0:
            self.resetDisplay()
            return

        # Figure out the scaling factor that
        # would preserve the current zoom
        # level for the new display bounds.
        xmin, xmax, ymin, ymax = glroutines.preserveAspectRatio(
            width, height, xmin, xmax, ymin, ymax)

        scale = opts.displayBounds.xlen / (xmax - xmin)

        # Adjust the zoom value so that the
        # effective zoom stays the same
        with props.suppress(opts, 'zoom'):
            opts.zoom = self.scaleToZoom(scale)


    def _displaySpaceChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` changes. Resets
        the display bounds and zoom.
        """
        self.resetDisplay()


    def _zoomChanged(self, *a):
        """Called when the :attr:`zoom` property changes. Updates the
        display bounds.
        """
        opts = self.opts
        loc = [opts.pos[opts.xax], opts.pos[opts.yax]]
        self._updateDisplayBounds(oldLoc=loc)


    def zoomToScale(self, zoom):
        """Converts the given zoom value into a scaling factor that can be
        multiplied by the display bounds width/height.

        Zoom is specified as a percentage.  At 100% the full scene takes up
        the full display.

        In order to make the zoom smoother at low levels, we re-scale the zoom
        value to be exponential across the range.

        This is done by transforming the zoom from ``[zmin, zmax]`` into
        ``[0.0, 1.0]``, then turning it from linear ``[0.0, 1.0]`` to
        exponential ``[0.0, 1.0]``, and then finally transforming it back to
        ``[zmin - zmax]``.

        However there is a slight hack in that, if the zoom value is less than
        100%, it will be applied linearly (i.e. 50% will cause the width/height
        to be scaled by 50%).
        """

        # Assuming that minval == 100.0
        opts = self.opts
        zmin = opts.getAttribute('zoom', 'minval')
        zmax = opts.getAttribute('zoom', 'maxval')
        zlen = zmax - zmin

        # Don't break the maths below
        if zoom <= 0:
            zoom = 1

        # Normal behaviour
        if zoom >= 100:

            # [100 - zmax] -> [0.0 - 1.0] -> exponentify -> [100 - zmax]
            zoom = (zoom - zmin)      / zlen
            zoom = zmin + (zoom ** 3) * zlen

            # Then we transform the zoom from
            # [100 - zmax] to [1.0 - 0.0] -
            # this value is used to scale the
            # bounds.
            scale = zmin / zoom

        # Hack for zoom < 100
        else:
            scale = 100.0 / zoom

        return scale


    def scaleToZoom(self, scale):
        """Converts the given zoom scaling factor into a zoom percentage.
        This method performs the reverse operation to the :meth:`zoomToScale`
        method.
        """

        opts = self.opts
        zmin = opts.getAttribute('zoom', 'minval')
        zmax = opts.getAttribute('zoom', 'maxval')
        zlen = zmax - zmin

        if scale > 1:
            zoom = 100.0 / scale

        else:

            # [100 - zmax] -> [0.0 - 1.0] -> de-exponentify -> [100 - zmax]
            zoom = zmin / scale
            zoom = (zoom - zmin) / zlen
            zoom = np.power(zoom, 1.0 / 3.0)
            zoom = zmin + zoom * zlen

        return zoom


    def _applyZoom(self, xmin, xmax, ymin, ymax):
        """*Zooms* in to the given rectangle according to the current value
        of the zoom property Returns a 4-tuple containing the updated bound
        values.
        """

        zoomFactor = self.zoomToScale(self.opts.zoom)

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

        opts = self.opts

        if bbox is None:
            bbox = (self.displayCtx.bounds.getLo(opts.xax),
                    self.displayCtx.bounds.getHi(opts.xax),
                    self.displayCtx.bounds.getLo(opts.yax),
                    self.displayCtx.bounds.getHi(opts.yax))

        xmin = bbox[0]
        xmax = bbox[1]
        ymin = bbox[2]
        ymax = bbox[3]

        # Save the display bounds in case
        # we need to preserve them with
        # respect to the current display
        # location.
        width, height                      = self.GetSize()
        oldxmin, oldxmax, oldymin, oldymax = opts.displayBounds[:]

        log.debug('{}: Required display bounds: '
                  'X: ({: 5.1f}, {: 5.1f}) Y: ({: 5.1f}, {: 5.1f})'.format(
                      opts.zax, xmin, xmax, ymin, ymax))

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
            xloc = opts.pos[opts.xax]
            yloc = opts.pos[opts.yax]

            xlen = xmax - xmin
            ylen = ymax - ymin

            xmin = xloc - oldxoff * xlen
            ymin = yloc - oldyoff * ylen

            xmax = xmin + xlen
            ymax = ymin + ylen

        log.debug('{}: Final display bounds: '
                  'X: ({: 5.1f}, {: 5.1f}) Y: ({: 5.1f}, {: 5.1f})'.format(
                      opts.zax, xmin, xmax, ymin, ymax))

        opts.displayBounds[:] = (xmin, xmax, ymin, ymax)


    def _setViewport(self, invertX=None, invertY=None):
        """Calculates the GL bounds, projection, and model view matrices. They
        are stored as attributes which are accessible via the
        :meth:`viewport`, :meth:`projectionMatrix` and :meth:`viewMatrix`
        methods.

        :arg invertX: Invert the X axis. If not provided, taken from
                      :attr:`invertX`.

        :arg invertY: Invert the Y axis. If not provided, taken from
                      :attr:`invertY`.
        """

        opts          = self.opts
        xax           = opts.xax
        yax           = opts.yax
        zax           = opts.zax
        xmin          = opts.displayBounds.xlo
        xmax          = opts.displayBounds.xhi
        ymin          = opts.displayBounds.ylo
        ymax          = opts.displayBounds.yhi
        zmin          = self.displayCtx.bounds.getLo(zax)
        zmax          = self.displayCtx.bounds.getHi(zax)

        if invertX is None: invertX = opts.invertX
        if invertY is None: invertY = opts.invertY

        # If there is  no space to draw, do nothing
        if (xmin == xmax) or (ymin == ymax):
            self.__viewport         = None
            self.__projectionMatrix = None
            self.__viewMatrix       = None
            return

        # Add a bit of padding to the depth limits
        zmin -= 1e-3
        zmax += 1e-3

        lo = [None] * 3
        hi = [None] * 3

        lo[xax], hi[xax] = xmin, xmax
        lo[yax], hi[yax] = ymin, ymax
        lo[zax], hi[zax] = zmin, zmax

        # calculate projection and mv
        # matrices for 2D ortho
        projmat, mvmat = glroutines.show2D(
            xax, yax, lo, hi, invertX, invertY)

        # store a copy of the final bounds and
        # proj/mv matrices interested parties can
        # retrieve them via the viewport/
        # projectionMatrix/ viewMatrix methods.
        self.__viewport         = [(lo[0], hi[0]), (lo[1], hi[1]), (lo[2], hi[2])]
        self.__projectionMatrix = projmat
        self.__viewMatrix       = mvmat


    def _drawCursor(self):
        """Draws a green cursor at the current X/Y position."""

        copts      = self.opts
        ovl        = self.displayCtx.getSelectedOverlay()
        xmin, xmax = self.displayCtx.bounds.getRange(copts.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(copts.yax)
        x          = copts.pos[copts.xax]
        y          = copts.pos[copts.yax]
        lines      = []

        # Just show a vertical line at xpos,
        # and a horizontal line at ypos
        if not copts.cursorGap:
            lines.append((x,    ymin, x,    ymax))
            lines.append((xmin, y,    xmax, y))

        # Draw vertical/horizontal cursor lines,
        # with a gap at the cursor centre

        # Not a NIFTI image - just
        # use a fixed gap size
        elif ovl is None or not isinstance(ovl, fslimage.Nifti):

            lines.append((xmin,    y,       x - 0.5, y))
            lines.append((x + 0.5, y,       xmax,    y))
            lines.append((x,       ymin,    x,       y - 0.5))
            lines.append((x,       y + 0.5, x,       ymax))

        # If the current overlay is NIFTI, make
        # the gap size match its voxel size
        else:

            # Get the current voxel
            # coordinates,
            dopts = self.displayCtx.getOpts(ovl)
            vox   = dopts.getVoxel(vround=False)

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
                axes = ovl.axisMapping(dopts.getTransform('voxel', 'display'))
                axes = np.abs(axes) - 1
                xax  = axes[copts.xax]
                yax  = axes[copts.yax]

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
                vloc  = dopts.transformCoords(vox,  'voxel', 'display')
                vlocx = dopts.transformCoords(voxx, 'voxel', 'display')
                vlocy = dopts.transformCoords(voxy, 'voxel', 'display')

                xlow  = min(vloc[copts.xax], vlocx[copts.xax])
                xhigh = max(vloc[copts.xax], vlocx[copts.xax])
                ylow  = min(vloc[copts.yax], vlocy[copts.yax])
                yhigh = max(vloc[copts.yax], vlocy[copts.yax])

            lines.append((xmin,  y,     xlow, y))
            lines.append((xhigh, y,     xmax, y))
            lines.append((x,     ymin,  x,    ylow))
            lines.append((x,     yhigh, x,    ymax))

        kwargs = {
            'colour'     : copts.cursorColour,
            'lineWidth'  : copts.cursorWidth
        }

        for line in lines:
            self._annotations.line(*line, **kwargs)
            self._annotations.line(*line, **kwargs)


    def _draw(self, *a):
        """Draws the current scene to the canvas. """

        if self.destroyed:
            return

        width, height = self.GetScaledSize()
        copts         = self.opts
        zpos          = copts.pos[copts.zax]
        axes          = (copts.xax, copts.yax, copts.zax)

        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        gl.glViewport(0, 0, width, height)
        glroutines.clear(copts.bgColour)

        overlays, globjs = self._getGLObjects()

        if len(overlays) == 0:
            return

        # Calculate viewport bounds and
        # projection/modelview matrices
        self._setViewport()
        if self.projectionMatrix is None:
            return

        # Do not draw anything if some globjects
        # are not ready. This is because, if a
        # GLObject was drawn, but is now temporarily
        # not ready (e.g. it has an image texture
        # that is being asynchronously refreshed),
        # drawing the scene now would cause
        # flickering of that GLObject.
        if len(globjs) == 0 or any(not g.ready() for g in globjs):
            return

        for overlay, globj in zip(overlays, globjs):

            display = self.displayCtx.getDisplay(overlay)
            if not display.enabled:
                continue

            log.debug('Drawing %u slice for overlay %s',
                      copts.zax, display.name)

            globj.preDraw()
            globj.draw2D(self, zpos, axes)
            globj.postDraw()

        if copts.showCursor:
            self._drawCursor()

        self._annotations.draw2D(zpos, axes)
