#!/usr/bin/env python
#
# lightboxcanvas.py - The LightBoxCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxCanvas` class, which is a
:class:`.SliceCanvas` that displays multiple 2D slices along a single axis
from a collection of 3D overlays.
"""

import sys
import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.data.image                    as fslimage
import fsl.utils.transform               as transform

import fsleyes.displaycontext.canvasopts as canvasopts
import fsleyes.gl.slicecanvas            as slicecanvas
import fsleyes.gl.resources              as glresources
import fsleyes.gl.routines               as glroutines
import fsleyes.gl.textures               as textures


log = logging.getLogger(__name__)


class LightBoxCanvas(slicecanvas.SliceCanvas):
    """The ``LightBoxCanvas`` represents an OpenGL canvas which displays
    multiple slices from a collection of 3D overlays. The slices are laid
    out on the same canvas along rows and columns, with the slice at the
    minimum Z position translated to the top left of the canvas, and the
    slice with the maximum Z value translated to the bottom right.


    .. note:: The :class:`LightBoxCanvas` class is not intended to be
              instantiated directly - use one of these subclasses, depending
              on your use-case:

               - :class:`.OSMesaLightBoxCanvas` for static off-screen
                 rendering of a scene using OSMesa.

               - :class:`.WXGLLightBoxCanvas` for interactive rendering on a
                 :class:`wx.glcanvas.GLCanvas` canvas.


    The ``LightBoxCanvas`` class derives from the :class:`.SliceCanvas` class,
    and is tightly coupled to the ``SliceCanvas`` implementation.  Various
    settings, and the current scene displayed on a ``LightBoxCanvas``
    instance, can be changed through the properties of the
    ``LightBoxCanvasOpts`` instance, available via the :attr:`opts` attribute.


    Performance of a ``LightBoxCanvas`` instance may be controlled through the
    :attr:`.SliceCanvasOpts.renderMode` property, in the same way as for the
    :class:`.SliceCanvas`. However, the ``LightBoxCanvas`` handles the
    ``offscreen`` render mode differently to the ``SliceCanvas. Where the
    ``SliceCanvas`` uses a separate :class:`.RenderTexture` for every overlay
    in the :class:`.OverlayList`, the ``LightBoxCanvas`` uses a single
    ``RenderTexture`` to render all overlays off-screen.


    The ``LightBoxCanvas`` class defines the following convenience methods (in
    addition to those defined in the ``SliceCanvas`` class):

    .. autosummary::
       :nosignatures:

       canvasToWorld
       worldToCanvas
       getTotalRows
       calcSliceSpacing
    """


    def __init__(self, overlayList, displayCtx, zax=0):
        """Create a ``LightBoxCanvas`` object.

        :arg overlayList: An :class:`.OverlayList` object which contains a
                          list of overlays to be displayed.

        :arg displayCtx: A :class:`.DisplayContext` object which defines how
                         that overlay list is to be displayed.

        :arg zax:        Display coordinate system axis to be used as the
                         'depth' axis. Can be changed via the
                         :attr:`.SliceCanvas.zax` property.
        """

        # These attributes are used to keep track of
        # the total number of slices to be displayed,
        # and the total number of rows to be displayed
        self._nslices   = 0
        self._totalRows = 0

        # The final display bounds calculated by
        # SliceCanvas._updateDisplayBounds is not
        # necessarily the same as the actual bounds,
        # as they are  adjusted to preserve  the
        # image aspect ratio. But the real bounds
        # are of use in the _zPosChanged method, so
        # we save them here as an attribute -
        # see _updateDisplayBounds.
        self._realBounds = None

        # This will point to a RenderTexture if
        # the offscreen render mode is enabled
        self._offscreenRenderTexture = None

        opts = canvasopts.LightBoxCanvasOpts()

        slicecanvas.SliceCanvas.__init__(self,
                                         overlayList,
                                         displayCtx,
                                         zax,
                                         opts)

        opts.addListener('sliceSpacing',   self.name, self._slicePropsChanged)
        opts.addListener('ncols',          self.name, self._slicePropsChanged)
        opts.addListener('nrows',          self.name, self._slicePropsChanged)
        opts.addListener('zrange',         self.name, self._slicePropsChanged)
        opts.addListener('showGridLines',  self.name, self.Refresh)
        opts.addListener('highlightSlice', self.name, self.Refresh)
        opts.addListener('topRow',         self.name, self._topRowChanged)

        # Add a listener to the position so when it
        # changes we can adjust the display range (via
        # the topRow property) to ensure the slice
        # corresponding to the current z position is
        # visible. SliceCanvas.__init__ has already
        # registered a listener, on pos, with
        # self.name - so we use a different name
        # here
        opts.addListener('pos',
                         '{}_zPosChanged'.format(self.name),
                         self._zPosChanged)


    def destroy(self):
        """Overrides :meth:`.SliceCanvas.destroy`. Must be called when this
        ``LightBoxCanvas`` is no longer needed.

        Removes some property listeners, makes sure that the off screen
        :class:`.RenderTexture` (if one exists) is destroyed, and then calls
        the :meth:`.SliceCanvas.destroy` method.
        """

        opts = self.opts

        opts.removeListener('pos', '{}_zPosChanged'.format(self.name))
        opts.removeListener('sliceSpacing',                self.name)
        opts.removeListener('ncols',                       self.name)
        opts.removeListener('nrows',                       self.name)
        opts.removeListener('zrange',                      self.name)
        opts.removeListener('showGridLines',               self.name)
        opts.removeListener('highlightSlice',              self.name)
        opts.removeListener('topRow',                      self.name)

        if self._offscreenRenderTexture is not None:
            self._offscreenRenderTexture.destroy()

        slicecanvas.SliceCanvas.destroy(self)


    def worldToCanvas(self, pos):
        """Given an x/y/z location in the display coordinate system, converts
        it into an x/y position, in the coordinate system of this
        ``LightBoxCanvas``.
        """
        opts    = self.opts
        xpos    = pos[opts.xax]
        ypos    = pos[opts.yax]
        zpos    = pos[opts.zax]
        sliceno = int(np.floor((zpos - opts.zrange.xlo) / opts.sliceSpacing))

        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)
        xmin = self.displayCtx.bounds.getLo( opts.xax)
        ymin = self.displayCtx.bounds.getLo( opts.yax)

        row = self._totalRows - int(np.floor(sliceno / opts.ncols)) - 1
        col =                   int(np.floor(sliceno % opts.ncols))

        if opts.invertX: xpos = xmin + xlen - (xpos - xmin)
        if opts.invertY: ypos = ymin + ylen - (ypos - ymin)

        xpos = xpos + xlen * col
        ypos = ypos + ylen * row

        return xpos, ypos


    def canvasToWorld(self, xpos, ypos):
        """Overrides :meth:.SliceCanvas.canvasToWorld`.

        Given pixel x/y coordinates on this canvas, translates them into the
        corresponding display space x/y/z coordinates.  Returns a 3-tuple
        containing the (x, y, z) display system coordinates. If the given
        canvas position is out of the :attr:`.SliceCanvas.displayBounds`,
        ``None`` is returned.
        """

        opts  = self.opts
        nrows = self._totalRows
        ncols = opts.ncols

        screenPos = slicecanvas.SliceCanvas.canvasToWorld(
            self, xpos, ypos, invertX=False, invertY=False)

        if screenPos is None:
            return None

        screenx = screenPos[opts.xax]
        screeny = screenPos[opts.yax]

        xmin = self.displayCtx.bounds.getLo( opts.xax)
        ymin = self.displayCtx.bounds.getLo( opts.yax)
        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)

        xmax = xmin + ncols * xlen
        ymax = ymin + nrows * ylen

        col     =         int(np.floor((screenx - xmin) / xlen))
        row     = nrows - int(np.floor((screeny - ymin) / ylen)) - 1
        sliceno = row * ncols + col

        if screenx <  xmin or \
           screenx >  xmax or \
           screeny <  ymin or \
           screeny >  ymax or \
           sliceno <  0    or \
           sliceno >= self._nslices:
            return None

        xpos = screenx  -          col      * xlen
        ypos = screeny  - (nrows - row - 1) * ylen

        if opts.invertX: xpos = xlen - (xpos - xmin) + xmin
        if opts.invertY: ypos = ylen - (ypos - ymin) + ymin

        zpos = opts.zrange.xlo + (sliceno + 0.5) * opts.sliceSpacing

        pos           = [0, 0, 0]
        pos[opts.xax] = xpos
        pos[opts.yax] = ypos
        pos[opts.zax] = zpos

        return tuple(pos)


    def getTotalRows(self):
        """Returns the total number of rows that may be displayed. """
        return self._totalRows


    def calcSliceSpacing(self, overlay):
        """Calculates and returns a Z-axis slice spacing value suitable
        for the given overlay.
        """
        copts      = self.opts
        displayCtx = self.displayCtx
        dopts      = displayCtx.getOpts(overlay)
        zmin, zmax = dopts.bounds.getRange(copts.zax)
        overlay    = displayCtx.getReferenceImage(overlay)

        # If the overlay does not have a
        # reference NIFTI image, choose
        # an arbitrary slice spacing.
        if overlay is None:
            return (zmax - zmin) / 50.0

        # Get the DisplayOpts instance
        # for the reference image
        dopts = displayCtx.getOpts(overlay)

        # Otherwise return a spacing
        # appropriate for the current
        # display space
        if   dopts.transform == 'id':          return 1
        elif dopts.transform == 'pixdim':      return overlay.pixdim[copts.zax]
        elif dopts.transform == 'pixdim-flip': return overlay.pixdim[copts.zax]
        elif dopts.transform == 'affine':      return min(overlay.pixdim[:3])

        # This overlay is being displayed with a
        # custrom transformation matrix  - check
        # to see what display space we're in
        displaySpace = displayCtx.displaySpace

        if isinstance(displaySpace, fslimage.Nifti) and \
           overlay is not displaySpace:
            return self.calcSliceSpacing(displaySpace)
        else:
            return min(overlay.pixdim[:3])


    def _zAxisChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._zAxisChanged`. Calls that
        method, and then resets the :attr:`sliceSpacing` and :attr:`zrange`
        properties to sensible values.
        """
        slicecanvas.SliceCanvas._zAxisChanged(self, *a)
        self._updateZAxisProperties()
        self._slicePropsChanged()


    def _topRowChanged(self, *a):
        """Called when the :attr:`topRow` property changes.  Adjusts display
        range and refreshes the canvas.
        """
        self._updateDisplayBounds()
        self.Refresh()


    def _slicePropsChanged(self, *a):
        """Called when any of the slice properties change. Regenerates slice
        locations and display bounds, and refreshes the canvas.
        """

        self._calcNumSlices()
        self._genSliceLocations()
        self._zPosChanged()
        self._updateDisplayBounds()

        if log.getEffectiveLevel() == logging.DEBUG:
            opts  = self.opts
            props = [('nrows',        opts.nrows),
                     ('ncols',        opts.ncols),
                     ('sliceSpacing', opts.sliceSpacing),
                     ('zrange',       opts.zrange)]

            props = '; '.join(['{}={}'.format(k, v) for k, v in props])

            log.debug('Lightbox properties changed: [{}]'.format(props))

        self.Refresh()


    def _renderModeChange(self, *a):
        """Overrides :meth:`.SliceCanvas._renderModeChange`. Makes sure that
        any off-screen :class:`.RenderTexture` is destroyed, and calls the
        :meth:`.SliceCanvas._renderModeChange` method.
        """

        if self._offscreenRenderTexture is not None:
            self._offscreenRenderTexture.destroy()
            self._offscreenRenderTexture = None

        slicecanvas.SliceCanvas._renderModeChange(self, *a)


    def _updateRenderTextures(self):
        """Overrides :meth:`.SliceCanvas._updateRenderTextures`.
        Destroys/creates :class:`.RenderTexture` and
        :class:`.RenderTextureStack` instances as needed.
        """

        renderMode = self.opts.renderMode

        if renderMode == 'onscreen':
            return

        # The LightBoxCanvas does offscreen rendering
        # a bit different to the SliceCanvas. The latter
        # uses a separate render texture for each overlay
        # whereas here we're going to use a single
        # render texture for all overlays.
        elif renderMode == 'offscreen':
            if self._offscreenRenderTexture is not None:
                self._offscreenRenderTexture.destroy()

            self._offscreenRenderTexture = textures.RenderTexture(
                '{}_{}'.format(type(self).__name__, id(self)),
                gl.GL_LINEAR)

            self._offscreenRenderTexture.setSize(768, 768)

        # The LightBoxCanvas handles pre-render mode
        # the same way as the SliceCanvas - a separate
        # RenderTextureStack for eacn globject
        elif renderMode == 'prerender':

            # Delete any RenderTextureStack instances for
            # overlays which have been removed from the list
            for overlay, (tex, name) in list(self._prerenderTextures.items()):
                if overlay not in self.overlayList:
                    self._prerenderTextures.pop(overlay)
                    glresources.delete(name)

            # Create a RendeTextureStack for overlays
            # which have been added to the list
            for overlay in self.overlayList:
                if overlay in self._prerenderTextures:
                    continue

                globj = self._glObjects.get(overlay, None)

                if (globj is None) or (not globj):
                    continue

                rt, name = self._getPreRenderTexture(globj, overlay)
                self._prerenderTextures[overlay] = rt, name

        self.Refresh()


    def _calcNumSlices(self, *a):
        """Calculates the total number of slices to be displayed and
        the total number of rows.
        """

        opts = self.opts
        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)
        zlen = opts.zrange.xlen
        width, height = self.GetSize()

        if xlen   == 0 or \
           ylen   == 0 or \
           width  == 0 or \
           height == 0:
            return

        self._nslices   = int(np.ceil(zlen / opts.sliceSpacing))
        self._totalRows = int(np.ceil(self._nslices / float(opts.ncols)))

        if self._nslices == 0 or self._totalRows == 0:
            return

        # All slices are going to be displayed, so
        # we'll 'disable' the topRow property
        if self._totalRows < opts.nrows:
            opts.setAttribute('topRow', 'minval', 0)
            opts.setAttribute('topRow', 'maxval', 0)

        # nrows slices are going to be displayed,
        # and the topRow property can be used to
        # scroll through all available rows.
        else:
            opts.setAttribute('topRow', 'maxval', self._totalRows - opts.nrows)


    def _zPosChanged(self, *a):
        """Called when the :attr:`.SliceCanvas.pos` ``z`` value changes.

        Makes sure that the corresponding slice is visible.
        """

        # figure out where we are in the canvas world
        opts             = self.opts
        canvasX, canvasY = self.worldToCanvas(opts.pos.xyz)

        # Get the actual canvas bounds
        xlo, xhi, ylo, yhi = self._realBounds

        # already in bounds
        if canvasX >= xlo and \
           canvasX <= xhi and \
           canvasY >= ylo and \
           canvasY <= yhi:
            return

        # figure out what row we're on
        zpos    = opts.pos[opts.zax]
        sliceno = int(np.floor((zpos - opts.zrange.xlo) / opts.sliceSpacing))
        row     = int(np.floor(sliceno / opts.ncols))

        # and make sure that row is visible
        opts.topRow = row


    def _overlayListChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._overlayListChanged`.

        Regenerates slice locations for all overlays, and calls the
        :meth:`.SliceCanvas._overlayListChanged` method.
        """
        self._updateZAxisProperties()
        self._genSliceLocations()
        slicecanvas.SliceCanvas._overlayListChanged(self, *a)


    def _updateZAxisProperties(self):
        """Called by the :meth:`_overlayListChanged` and
        :meth:`_overlayBoundsChanged` methods.

        Updates the constraints (minimum/maximum values) of the
        :attr:`sliceSpacing` and :attr:`zrange` properties.
        """

        opts = self.opts

        if len(self.overlayList) == 0:
            opts.setAttribute('zrange', 'minDistance', 0)
            opts.zrange.x     = (0, 0)
            opts.sliceSpacing = 0
            return

        # Get the new Z range from the
        # display context bounding box.
        #
        # And calculate the minimum possible
        # slice spacing - the smallest pixdim
        # across all overlays in the list.
        newZRange = self.displayCtx.bounds.getRange(opts.zax)
        newZGap   = sys.float_info.max

        for overlay in self.overlayList:

            zgap = self.calcSliceSpacing(overlay)

            if zgap < newZGap:
                newZGap = zgap

        # Update the zrange and slice
        # spacing constraints
        opts.zrange.setLimits(0, *newZRange)
        opts.setAttribute('zrange',       'minDistance', newZGap)
        opts.setAttribute('sliceSpacing', 'minval',      newZGap)


    def _overlayBoundsChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._overlayBoundsChanged`.

        Called when the :attr:`.DisplayContext.bounds` change. Updates the
        :attr:`zrange` min/max values.
        """

        slicecanvas.SliceCanvas._overlayBoundsChanged(self, preserveZoom=False)

        self._updateZAxisProperties()
        self._calcNumSlices()
        self._genSliceLocations()


    def _updateDisplayBounds(self, *args, **kwargs):
        """Overrides :meth:`.SliceCanvas._updateDisplayBounds`.

        Called on canvas resizes, display bound changes and lightbox slice
        property changes. Calculates the required bounding box that is to
        be displayed, in display coordinates.
        """

        opts = self.opts
        xmin = self.displayCtx.bounds.getLo( opts.xax)
        ymin = self.displayCtx.bounds.getLo( opts.yax)
        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)

        # Calculate the vertical offset required to
        # ensure that the current 'topRow' is the first
        # row, and the correct number of rows ('nrows')
        # are displayed

        # if the number of rows to be displayed (nrows)
        # is more than the number of rows that exist
        # (totalRows), calculate an offset to vertically
        # centre the existing row space in the display
        # row space
        if self._totalRows < opts.nrows:
            off  = (self._totalRows - opts.nrows) / 2.0

        # otherwise calculate the offset so that the
        # top of the display space lines up with the
        # current topRow
        else:
            off  = self._totalRows - opts.nrows - opts.topRow

        ymin = ymin + ylen * off
        xmax = xmin + xlen * opts.ncols
        ymax = ymin + ylen * opts.nrows

        # Save the real canvas bounds
        self._realBounds = (xmin, xmax, ymin, ymax)

        log.debug('Required lightbox bounds: X: ({}, {}) Y: ({}, {})'.format(
            xmin, xmax, ymin, ymax))

        slicecanvas.SliceCanvas._updateDisplayBounds(
            self, (xmin, xmax, ymin, ymax))


    def _genSliceLocations(self):
        """Called when any of the slice display properties change.

        For every overlay in the overlay list, generates a list of
        transformation matrices, and a list of slice indices. The latter
        specifies the slice indices from the overlay to be displayed, and the
        former specifies the transformation matrix to be used to position the
        slice on the canvas.
        """

        # calculate the locations, in display coordinates,
        # of all slices to be displayed on the canvas
        opts      = self.opts
        sliceLocs = np.arange(
            opts.zrange.xlo + opts.sliceSpacing * 0.5,
            opts.zrange.xhi,
            opts.sliceSpacing)

        self._sliceLocs  = {}
        self._transforms = {}

        # calculate the transformation for each
        # slice in each overlay, and the index of
        # each slice to be displayed
        for i, overlay in enumerate(self.overlayList):

            iSliceLocs  = []
            iTransforms = []

            for zi, zpos in enumerate(sliceLocs):

                xform = self._calculateSliceTransform(overlay, zi)

                iTransforms.append(xform)
                iSliceLocs .append(zpos)

            self._transforms[overlay] = iTransforms
            self._sliceLocs[ overlay] = iSliceLocs


    def _calculateSliceTransform(self, overlay, sliceno):
        """Calculates a transformation matrix for the given slice number in
        the given overlay.

        Each slice is displayed on the same canvas, but is translated to a
        specific row/column.  So translation matrix is created, to position
        the slice in the correct location on the canvas.
        """

        opts  = self.opts
        nrows = self._totalRows
        ncols = opts.ncols

        row = int(np.floor(sliceno / ncols))
        col = int(np.floor(sliceno % ncols))

        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)

        translate              = np.identity(4, dtype=np.float32)
        translate[opts.xax, 3] = xlen * col
        translate[opts.yax, 3] = ylen * (nrows - row - 1)
        translate[opts.zax, 3] = 0

        return translate


    def __prepareSliceTransforms(self, globj, xforms):
        """Applies the :attr:`.SliceCanvas.invertX` and
        :attr:`.SliceCanvas.invertY` properties to the given transformation
        matrices, if necessary. Returns the transformations.
        """

        opts = self.opts

        if not opts.invertX or opts.invertY:
            return xforms

        invXforms = []
        lo, hi    = globj.getDisplayBounds()
        xmin      = lo[opts.xax]
        xmax      = hi[opts.xax]
        ymin      = lo[opts.yax]
        ymax      = hi[opts.yax]
        xlen      = xmax - xmin
        ylen      = ymax - ymin

        # We have to translate each slice transformation
        # to the origin, perform the flip there, then
        # transform it back to its original location.
        for xform in xforms:

            invert     = np.eye(4)
            toOrigin   = np.eye(4)
            fromOrigin = np.eye(4)

            xoff = xlen / 2.0 + xform[opts.xax, 3] + xmin
            yoff = ylen / 2.0 + xform[opts.yax, 3] + ymin

            if opts.invertX:
                invert[    opts.xax, opts.xax] = -1
                toOrigin[  opts.xax, 3]        = -xoff
                fromOrigin[opts.xax, 3]        =  xoff
            if opts.invertY:
                invert[    opts.yax, opts.yax] = -1
                toOrigin[  opts.yax, 3]        = -yoff
                fromOrigin[opts.yax, 3]        =  yoff

            xform = transform.concat(fromOrigin,
                                     invert,
                                     toOrigin,
                                     xform)
            invXforms.append(xform)

        return invXforms


    def _drawGridLines(self):
        """Draws grid lines between all the displayed slices."""

        opts = self.opts

        if self._totalRows == 0 or opts.ncols == 0:
            return

        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)
        xmin = self.displayCtx.bounds.getLo( opts.xax)
        ymin = self.displayCtx.bounds.getLo( opts.yax)

        rowLines = np.zeros(((self._totalRows - 1) * 2, 2), dtype=np.float32)
        colLines = np.zeros(((opts.ncols      - 1) * 2, 2), dtype=np.float32)

        topRow = self._totalRows - opts.topRow
        btmRow = topRow          - self._totalRows

        rowLines[:, 1] = np.arange(
            ymin + (btmRow + 1) * ylen,
            ymin +  topRow      * ylen, ylen).repeat(2)

        rowLines[:, 0] = np.tile(
            np.array([xmin, xmin + opts.ncols * xlen]),
            self._totalRows - 1)

        colLines[:, 0] = np.arange(
            xmin + xlen,
            xmin + xlen * opts.ncols, xlen).repeat(2)

        colLines[:, 1] = np.tile(np.array([
            ymin + btmRow * ylen,
            ymin + topRow * ylen]), opts.ncols - 1)

        colour = (0.3, 0.9, 1.0, 0.8)

        for lines in (rowLines, colLines):
            for i in range(0, len(lines), 2):
                self.getAnnotations().line(lines[i],
                                           lines[i + 1],
                                           colour=colour,
                                           width=2)


    def _drawSliceHighlight(self):
        """Draws a box around the slice which contains the current cursor
        location.
        """

        opts    = self.opts
        zpos    = opts.pos[opts.zax]
        sliceno = int(np.floor((zpos - opts.zrange.xlo) / opts.sliceSpacing))

        xlen    = self.displayCtx.bounds.getLen(opts.xax)
        ylen    = self.displayCtx.bounds.getLen(opts.yax)
        xmin    = self.displayCtx.bounds.getLo( opts.xax)
        ymin    = self.displayCtx.bounds.getLo( opts.yax)
        row     = int(np.floor(sliceno / opts.ncols))
        col     = int(np.floor(sliceno % opts.ncols))

        # don't draw the cursor if it is on a
        # non-existent or non-displayed slice
        if sliceno >  self._nslices:            return
        if row     <  opts.topRow:              return
        if row     >= opts.topRow + opts.nrows: return

        # in GL space, the top row is actually the bottom row
        row = self._totalRows - row - 1

        self.getAnnotations().rect((xmin + xlen * col,
                                    ymin + ylen * row),
                                   xlen,
                                   ylen,
                                   colour=(1, 0, 0),
                                   width=2)


    def _drawCursor(self):
        """Draws a cursor at the current canvas position (the
        :attr:`.SliceCanvas.pos` property).
        """

        opts    = self.opts
        zpos    = opts.pos[opts.zax]
        sliceno = int(np.floor((zpos - opts.zrange.xlo) / opts.sliceSpacing))
        xlen    = self.displayCtx.bounds.getLen(opts.xax)
        ylen    = self.displayCtx.bounds.getLen(opts.yax)
        xmin    = self.displayCtx.bounds.getLo( opts.xax)
        ymin    = self.displayCtx.bounds.getLo( opts.yax)
        row     = int(np.floor(sliceno / opts.ncols))
        col     = int(np.floor(sliceno % opts.ncols))

        # don't draw the cursor if it is on a
        # non-existent or non-displayed slice
        if sliceno >  self._nslices:            return
        if row     <  opts.topRow:              return
        if row     >= opts.topRow + opts.nrows: return

        # in GL space, the top row is actually the bottom row
        row = self._totalRows - row - 1

        xpos, ypos = self.worldToCanvas(opts.pos.xyz)

        xverts = np.zeros((2, 2))
        yverts = np.zeros((2, 2))

        xverts[:, 0] = xpos
        xverts[0, 1] = ymin + (row)     * ylen
        xverts[1, 1] = ymin + (row + 1) * ylen

        yverts[:, 1] = ypos
        yverts[0, 0] = xmin + (col)     * xlen
        yverts[1, 0] = xmin + (col + 1) * xlen

        annot = self.getAnnotations()

        kwargs = {
            'colour' : opts.cursorColour,
            'width'  : 1
        }

        annot.line(xverts[0], xverts[1], **kwargs)
        annot.line(yverts[0], yverts[1], **kwargs)


    def _draw(self, *a):
        """Draws the current scene to the canvas. """


        if self.destroyed():
            return

        width, height = self.GetSize()
        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        opts = self.opts
        axes = (opts.xax, opts.yax, opts.zax)

        overlays, globjs = self._getGLObjects()

        # See comment in SliceCanvas._draw
        # regarding this test
        if any([not g.ready() for g in globjs]):
            return

        if opts.renderMode == 'offscreen':

            log.debug('Rendering to off-screen texture')

            rt = self._offscreenRenderTexture

            lo = [None] * 3
            hi = [None] * 3

            lo[opts.xax], hi[opts.xax] = opts.displayBounds.x
            lo[opts.yax], hi[opts.yax] = opts.displayBounds.y
            lo[opts.zax], hi[opts.zax] = opts.zrange

            rt.bindAsRenderTarget()
            rt.setRenderViewport(opts.xax, opts.yax, lo, hi)
            glroutines.clear((0, 0, 0, 0))

        else:
            self._setViewport(invertX=False, invertY=False)
            glroutines.clear(opts.bgColour)


        startSlice = opts.ncols * opts.topRow
        endSlice   = startSlice + opts.nrows * opts.ncols

        if endSlice > self._nslices:
            endSlice = self._nslices

        # Draw all the slices for all the overlays.
        for overlay, globj in zip(overlays, globjs):

            display = self.displayCtx.getDisplay(overlay)
            globj   = self._glObjects.get(overlay, None)

            if not display.enabled:
                continue

            log.debug('Drawing {} slices ({} - {}) for '
                      'overlay {} directly to canvas'.format(
                          endSlice - startSlice,
                          startSlice,
                          endSlice,
                          overlay))

            zposes = self._sliceLocs[ overlay][startSlice:endSlice]
            xforms = self._transforms[overlay][startSlice:endSlice]
            xforms = self.__prepareSliceTransforms(globj, xforms)

            if opts.renderMode == 'prerender':
                rt, name = self._prerenderTextures.get(overlay, (None, None))

                if rt is None:
                    continue

                log.debug('Drawing {} slices ({} - {}) for overlay {} '
                          'from pre-rendered texture'.format(
                              endSlice - startSlice,
                              startSlice,
                              endSlice,
                              overlay))

                for zpos, xform in zip(zposes, xforms):
                    rt.draw(zpos, xform)
            else:

                globj.preDraw()
                globj.drawAll(axes, zposes, xforms)
                globj.postDraw()

        if opts.renderMode == 'offscreen':
            rt.unbindAsRenderTarget()
            rt.restoreViewport()
            self._setViewport(invertX=False, invertY=False)
            glroutines.clear(opts.bgColour)
            rt.drawOnBounds(
                0,
                opts.displayBounds.xlo,
                opts.displayBounds.xhi,
                opts.displayBounds.ylo,
                opts.displayBounds.yHi,
                opts.xax,
                opts.yax)

        if len(self.overlayList) > 0:
            if opts.showCursor:     self._drawCursor()
            if opts.showGridLines:  self._drawGridLines()
            if opts.highlightSlice: self._drawSliceHighlight()

        self.getAnnotations().draw(opts.pos[opts.zax])
