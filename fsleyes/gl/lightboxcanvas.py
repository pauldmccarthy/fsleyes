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

import logging

import numpy     as np
import OpenGL.GL as gl

import fsleyes_props                     as props
import fsleyes.displaycontext.canvasopts as canvasopts
import fsleyes.gl.slicecanvas            as slicecanvas
import fsleyes.gl.routines               as glroutines
import fsleyes.gl.textures               as textures
import fsleyes.gl.lightboxlabels         as lblabels


log = logging.getLogger(__name__)


class LightBoxCanvas(slicecanvas.SliceCanvas):
    """The ``LightBoxCanvas`` represents an OpenGL canvas which displays
    multiple slices from a collection of 3D overlays. The slices are laid
    out on the same canvas along rows and columns, with the slice at the
    minimum Z position translated to the top left of the canvas, and the
    slice with the maximum Z value translated to the bottom right. A
    suitable number of rows and columns are automatically calculated
    whenever the canvas size is changed, or any
    :class:`.LightBoxCanvasOpts` properties change.

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
    ``SliceCanvas`` uses a separate :class:`.GLObjectRenderTexture` for every
    overlay in the :class:`.OverlayList`, the ``LightBoxCanvas`` uses a single
    :class:`.RenderTexture` to render all overlays off-screen.


    The ``LightBoxCanvas`` class defines the following convenience methods (in
    addition to those defined in the ``SliceCanvas`` class):

    .. autosummary::
       :nosignatures:

       canvasToWorld
       worldToCanvas
       calcSliceSpacing
    """


    def __init__(self, overlayList, displayCtx, zax=None):
        """Create a ``LightBoxCanvas`` object.

        :arg overlayList: An :class:`.OverlayList` object which contains a
                          list of overlays to be displayed.

        :arg displayCtx: A :class:`.DisplayContext` object which defines how
                         that overlay list is to be displayed.

        :arg zax:        Display coordinate system axis to be used as the
                         'depth' axis. Can be changed via the
                         :attr:`.SliceCanvas.zax` property.
        """

        # These attributes store the number of
        # rows/columns, Z bounds, position for
        # each slice, and affines encoding
        # vertical/horizontal offsets, which
        # position each slice on the canvas.
        self.__zbounds = [0, 0, 0]
        self.__zposes  = []
        self.__xforms  = []
        self.__nrows   = 0
        self.__ncols   = 0

        # This will point to a RenderTexture if
        # the offscreen render mode is enabled
        self._offscreenRenderTexture = None

        opts = canvasopts.LightBoxCanvasOpts()

        slicecanvas.SliceCanvas.__init__(self,
                                         overlayList,
                                         displayCtx,
                                         zax,
                                         opts)

        self.__labelMgr = lblabels.LightBoxLabels(self)

        opts.ilisten('sliceSpacing',   self.name, self._slicePropsChanged)
        opts.ilisten('zrange',         self.name, self._slicePropsChanged)
        opts.ilisten('nrows',          self.name, self._slicePropsChanged)
        opts.ilisten('ncols',          self.name, self._slicePropsChanged)
        opts.ilisten('invertX',        self.name, self._slicePropsChanged,
                     overwrite=True)
        opts.ilisten('invertY',        self.name, self._slicePropsChanged,
                     overwrite=True)
        opts. listen('showGridLines',  self.name, self.Refresh)
        opts. listen('highlightSlice', self.name, self.Refresh)


    def destroy(self):
        """Overrides :meth:`.SliceCanvas.destroy`. Must be called when this
        ``LightBoxCanvas`` is no longer needed.

        Removes some property listeners, makes sure that the off screen
        :class:`.RenderTexture` (if one exists) is destroyed, and then calls
        the :meth:`.SliceCanvas.destroy` method.
        """

        opts = self.opts
        name = self.name

        opts.remove('sliceSpacing',   name)
        opts.remove('zrange',         name)
        opts.remove('nrows',          name)
        opts.remove('ncols',          name)
        opts.remove('showGridLines',  name)
        opts.remove('highlightSlice', name)

        if self._offscreenRenderTexture is not None:
            self._offscreenRenderTexture.destroy()

        self.__labelMgr.destroy()
        self.__labelMgr = None

        slicecanvas.SliceCanvas.destroy(self)


    def gridPosition(self, pos=None):
        """Returns the slice, row, and column index of the current display
        location (from the :attr:`.SliceCanvas.pos` attribute).
        """

        opts    = self.opts
        bounds  = self.displayCtx.bounds
        ncols   = self.ncols
        zmin    = bounds.getLo( opts.zax)
        zlen    = bounds.getLen(opts.zax)

        if pos is None:
            pos = opts.pos

        if np.any(np.isclose(zlen, ncols)):
            return 0, 0, 0

        # Convert Z position into
        # slice/row/column indices
        zlo     = opts.normzrange[0]
        zpos    = pos[opts.zax]
        sliceno = (zpos - zmin) / zlen - zlo
        sliceno = int(np.floor(sliceno / opts.sliceSpacing))
        row     = int(np.floor(sliceno / ncols))
        col     = int(np.floor(sliceno % ncols))

        return sliceno, row, col


    @property
    def nrows(self):
        """Return the number of rows currently being displayed. """
        return self.__nrows


    @property
    def ncols(self):
        """Return the number of columns currently being displayed. """
        return self.__ncols


    @property
    def nslices(self):
        """Return the number of slices currently being displayed, equal
        to nrows * ncols. Note the distinction between this and
        :meth:`.LightBoxCanvasOpts.nslices`.
        """
        return self.nrows * self.ncols


    @property
    def maxrows(self):
        """Returns the total number of rows that would cover the full Z axis
        range. Used by the :class:`.LightBoxPanel` to implement scrolling.
        """
        if self.ncols == 0 or self.nrows == 0:
            return 0
        return int(np.ceil(self.opts.maxslices / self.ncols))


    @property
    def toprow(self):
        """Return the currently displayed top row, as an index relative to
        :meth:`maxrows`. Used by the :class:`.LightBoxPanel` to implement
        scrolling.
        """
        if self.ncols == 0 or self.nrows == 0:
            return 0
        return int(np.floor(self.opts.startslice / self.ncols))


    @property
    def zposes(self):
        """Return the Z coordinate of all current slices. The coordinates are
        in terms of the display coordinate system.
        """
        return self.__zposes


    def resetDisplay(self):
        """Overrides :meth:`.SliceCanvas.resetDisplay`.

        Resets the :attr:`zoom` to 100%, and sets the canvas display
        bounds to the overaly bounding box (from the
        :attr:`.DisplayContext.bounds`)
        """
        self.opts.zoom = 0
        self._regenGrid()


    def worldToCanvas(self, pos):
        """Given an x/y/z location in the display coordinate system, converts
        it into an x/y position, in the coordinate system of this
        ``LightBoxCanvas``.
        """

        opts        = self.opts
        xpos        = pos[opts.xax]
        ypos        = pos[opts.yax]
        nrows       = self.nrows
        bounds      = self.displayCtx.bounds
        xlen        = bounds.getLen(opts.xax)
        ylen        = bounds.getLen(opts.yax)
        xmin        = bounds.getLo( opts.xax)
        ymin        = bounds.getLo( opts.yax)
        _, row, col = self.gridPosition(pos)

        if row < 0           or \
           col < 0           or \
           row >= self.nrows or \
           col >= self.ncols:
            return None

        if opts.invertX: xpos = xmin + xlen - (xpos - xmin)
        if opts.invertY: ypos = ymin + ylen - (ypos - ymin)

        xpos = xpos + xlen * col
        ypos = ypos + ylen * (nrows - row - 1)

        return xpos, ypos


    def canvasToWorld(self, xpos, ypos):
        """Overrides :meth:.SliceCanvas.canvasToWorld`.

        Given pixel x/y coordinates on this canvas, translates them into the
        corresponding display space x/y/z coordinates.  Returns a 3-tuple
        containing the (x, y, z) display system coordinates. If the given
        canvas position is out of the :attr:`.SliceCanvas.displayBounds`,
        ``None`` is returned.
        """

        opts    = self.opts
        bounds  = self.displayCtx.bounds
        ncols   = self.ncols
        nrows   = self.nrows

        screenPos = slicecanvas.SliceCanvas.canvasToWorld(
            self, xpos, ypos, invertX=False, invertY=False)

        if screenPos is None:
            return None

        screenx = screenPos[opts.xax]
        screeny = screenPos[opts.yax]

        xmin = bounds.getLo( opts.xax)
        ymin = bounds.getLo( opts.yax)
        xlen = bounds.getLen(opts.xax)
        ylen = bounds.getLen(opts.yax)

        xmax = xmin + ncols * xlen
        ymax = ymin + nrows * ylen

        col     =         int(np.floor((screenx - xmin) / xlen))
        row     = nrows - int(np.floor((screeny - ymin) / ylen)) - 1
        sliceno = row * ncols + col

        if screenx <  xmin or \
           screenx >  xmax or \
           screeny <  ymin or \
           screeny >  ymax or \
           sliceno >= len(self.__zposes):
            return None

        xpos = screenx -          col      * xlen
        ypos = screeny - (nrows - row - 1) * ylen
        zpos = self.__zposes[sliceno]

        if opts.invertX: xpos = xlen - (xpos - xmin) + xmin
        if opts.invertY: ypos = ylen - (ypos - ymin) + ymin

        pos           = [0, 0, 0]
        pos[opts.xax] = xpos
        pos[opts.yax] = ypos
        pos[opts.zax] = zpos

        return tuple(pos)


    def sliceToWorld(self, slc):
        """Convert a slice index, or row/column indices, into a location in the
        display coordinate system.

        :arg slc: Slice index, or (row, column) tuple.

        :returns: A ``[x, y, z]`` position in the display coordinate system or
                  ``None`` if the slice is outside the bounds of the display
                  coordinate system.
        """

        opts    = self.opts
        bounds  = self.displayCtx.bounds
        nrows   = self.nrows
        ncols   = self.ncols
        nslices = len(self.zposes)
        xmin    = bounds.getLo( opts.xax)
        ymin    = bounds.getLo( opts.yax)
        xlen    = bounds.getLen(opts.xax)
        ylen    = bounds.getLen(opts.yax)

        if isinstance(slc, (list, tuple)):
            row, col = slc
            slc      = row * ncols + col
        else:
            row      = slc // ncols
            col      = slc %  ncols

        if slc >= nslices or row >= nrows or col >= ncols:
            return None

        # We position the x/y coordinates
        # at the slice centre
        pos           = [0] * 3
        pos[opts.xax] = xmin + 0.5 * xlen
        pos[opts.yax] = ymin + 0.5 * ylen
        pos[opts.zax] = self.zposes[slc]

        return pos


    def calcSliceSpacing(self, overlay):
        """Calculates and returns a minimum Z-axis slice spacing value suitable
        for the given overlay. The returned value is a proportion between 0 and
        1.
        """
        copts      = self.opts
        displayCtx = self.displayCtx
        dopts      = displayCtx.getOpts(overlay)
        overlay    = displayCtx.getReferenceImage(overlay)

        # If the overlay does not have a
        # reference NIFTI image, choose
        # an arbitrary slice spacing.
        if overlay is None:
            return 0.02

        # Get the DisplayOpts instance
        # for the reference image
        dopts = displayCtx.getOpts(overlay)

        # Otherwise return a spacing
        # appropriate for the current
        # display space
        #
        # display coordinate system
        # is orthogonal to image data
        # grid
        if dopts.transform in  ('id', 'pixdim', 'pixdim-flip'):
            return 1 / overlay.shape[copts.zax]

        # image may be rotated w.r.t.
        # display coordinate system
        else:
            return 1 / max(overlay.shape[:3])


    def calcGridSize(self):
        """Calculates a suitable slice grid size (number of rows and columns)
        based on the current canvas size, and number of slices to be displayed.
        Called by :meth:`_calculateSlices`.
        """

        w, h    = self.GetSize()
        bounds  = self.displayCtx.bounds
        opts    = self.opts
        xlen    = bounds.getLen(opts.xax)
        ylen    = bounds.getLen(opts.yax)
        nslices = opts.nslices

        if np.any(np.isclose([w, h, nslices, xlen, ylen], 0)):
            return 0, 0

        # Honour ncols/nrows (in that order
        # order of precedence) if they are set.
        if opts.ncols != 0:
            ncols  = opts.ncols
            nrows  = np.ceil(nslices / ncols).astype(int)
            return nrows, ncols
        elif opts.nrows != 0:
            nrows = opts.nrows
            ncols  = np.ceil(nslices / nrows).astype(int)
            return nrows, ncols

        # Otherwise automatically calculate
        # a grid size (nrows, ncols) which
        # minimises wasted canvas space.
        ncols = np.arange(1, nslices + 1).astype(int)
        nrows = np.ceil(nslices / ncols) .astype(int)

        # width/height of one slice
        slcw = w / ncols
        slch = slcw / (xlen / ylen)

        # choose nrows/ncols which takes
        # up full horizontal space (if possible)
        mask = (slch * nrows) <= h
        if sum(mask) > 0:
            nrows = nrows[mask]
            ncols = ncols[mask]
            slcw  = slcw[ mask]
            slch  = slch[ mask]

        # and which has smallest amount
        # of wasted canvas area
        waste = np.abs(w * h - slcw * slch * nrows * ncols)
        idx   = np.argmin(waste)

        return nrows[idx], ncols[idx]


    def _overlayListChanged(self):
        """Overrides :meth:`.SliceCanvas._overlayListChanged`. Sets
        some limits on some of the :class:`.LightBoxCanvasOpts` properties
        as needed.

        Specifically, the values of the ``LightBoxCanvasOpts.zrange`` and
        ``LightBoxCanvasOpts.sliceSpacing`` properties may be adjusted -  they
        are specified as proportions of the :attr:`.DisplayContext.bounds`,
        which means that they may have a different effect when the bounds
        change.
        """
        slicecanvas.SliceCanvas._overlayListChanged(self)

        if len(self.overlayList) == 0:
            return

        self._adjustSliceProps(True, True)
        self._regenGrid()


    def _renderModeChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._renderModeChanged`. Destroys/
        re-creates the off-screen :class:`.RenderTexture` as needed.
        """

        if self.opts.renderMode == 'onscreen':
            if self._offscreenRenderTexture is not None:
                self._offscreenRenderTexture.destroy()
                self._offscreenRenderTexture = None
        else:
            self._offscreenRenderTexture = textures.RenderTexture(
                f'{type(self).__name__}_{id(self)}',
                interp=gl.GL_LINEAR)
            self._offscreenRenderTexture.shape = 768, 768

        self.Refresh()


    def _zAxisChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._zAxisChanged`.  Called when the
        :attr:`.SliceCanvasOpts.zax` changes. Re-generates lightbox
        slices.
        """
        self._adjustSliceProps(False, True)
        self._regenGrid()


    def _slicePropsChanged(self, *a):
        """Called when any of the slice properties change. Regenerates slice
        locations and display bounds, and refreshes the canvas.
        """
        self._regenGrid()


    def _updateRenderTextures(self):
        """Overrides :meth:`.SliceCanvas._updateRenderTextures`. Does nothing.
        """


    def _overlayBoundsChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._overlayBoundsChanged`.

        Called when the :attr:`.DisplayContext.bounds` change. Re-generates
        slice locations.
        """
        self._regenGrid()


    def _adjustSliceProps(self, adjustZrange, adjustSpacing):
        """Called when the selected overlay changes, or the Z axis changes.
        Makes adjustments to the :attr:`.LightBoxCanvasOpts.zrange` and
        :attr:`.LightBoxCanvasOpts.sliceSpacing` properties to keep them
        consistent with respect to the currently selected overlay and
        display bounds.

        The ``zrange`` and ``sliceSpacing`` properties are defined in terms of
        the "slice coordinate system", having range 0 to 1. This means that
        their interpretation will be different depending on the properties of
        the Z axis in the display coordinate system. When the selected overlay
        changes, we don't want the displayed slices to change - this method
        adjusts the ``zrange`` and ``sliceSpacing`` values so that they will
        result in the same slices being displayed.

        This method is also called when the Z axis is changed. In this case,
        the ``sliceSpacing`` may have a different effect, e.g. for images with
        different FOVs / voxel resolutions along different axes. Therefore,
        the ``sliceSpacing`` property is also adjusted to remain consistent.
        """
        opts     = self.opts
        spacings = [self.calcSliceSpacing(o) for o in self.overlayList]
        spacing  = min(spacings)
        bounds   = self.displayCtx.bounds
        zmin     = bounds.getLo( opts.zax)
        zlen     = bounds.getLen(opts.zax)
        zpos     = opts.pos[opts.zax]

        # Adjust zrange and slice spacing so
        # that their effect is preserved if
        # the display bounds have changed
        zlo, zhi, sp = self.__zbounds
        preserve     = not ((zlo == 0) and (zhi == 0))

        if preserve:
            zlo = (zlo - zmin) / zlen
            zhi = (zhi - zmin) / zlen
            sp  = sp / zlen
        else:
            zpos = (zpos - zmin) / zlen
            zlo  = zpos - 0.1
            zhi  = zpos + 0.1
            sp   = spacing

        with props.skip(opts, ('sliceSpacing', 'zrange'), self.name):
            opts.setatt('sliceSpacing', 'minval', spacing)

            if adjustZrange:  opts.zrange.x     = zlo, zhi
            if adjustSpacing: opts.sliceSpacing = sp


    def _regenGrid(self):
        """Called by various property/event listeners. Re-generates slices and
        triggers a canvas refresh.
        """
        self._calculateSlices()
        self._updateDisplayBounds()
        self.Refresh()


    def _calculateSlices(self):
        """Calculates Z positions and affine transformations for each slice.
        The transformations are used to position each slice at a row/column
        on the canvas.
        """

        self.__nrows   = 0
        self.__ncols   = 0
        self.__zbounds = [0, 0, 0]
        self.__zposes  = []
        self.__xforms  = []

        w, h         = self.GetSize()
        bounds       = self.displayCtx.bounds
        opts         = self.opts
        nrows, ncols = self.calcGridSize()
        nslices      = nrows * ncols
        xlen         = bounds.getLen(opts.xax)
        ylen         = bounds.getLen(opts.yax)
        zlen         = bounds.getLen(opts.zax)
        zmin         = bounds.getLo( opts.zax)

        if np.any(np.isclose([w, h, nslices,
                              xlen, ylen, zlen,
                              len(self.overlayList)], 0)):
            return

        # calculate the locations, in display coordinates,
        # of all slices to be displayed on the canvas, and
        # calculate the X/Y transformation for each slice
        # to position it on the canvas
        start = opts.startslice
        end   = start + nslices
        self.__zposes = zmin + opts.slices[start:end] * zlen
        self.__xforms = []
        self.__nrows  = nrows
        self.__ncols  = ncols

        # record start/end slice locations and
        # spacing in absolute/display coordinates
        # rather than relative proportions, as
        # the _overlayListChanged method may need
        # to restore them.
        spacing        = zlen * opts.sliceSpacing
        zlo, zhi       = opts.normzrange
        zlo            = zmin + zlo * zlen
        zhi            = zmin + zhi * zlen
        self.__zbounds = [zlo, zhi, spacing]

        for sliceno in range(len(self.__zposes)):

            row                = int(np.floor(sliceno / ncols))
            col                = int(np.floor(sliceno % ncols))
            xform              = np.eye(4, dtype=np.float32)
            xform[opts.xax, 3] = xlen * col
            xform[opts.yax, 3] = ylen * (nrows - row - 1)
            xform[opts.zax, 3] = 0

            # apply opts.invertX/Y if necessary
            flipaxes = []
            if opts.invertX: flipaxes.append(opts.xax)
            if opts.invertY: flipaxes.append(opts.yax)
            if len(flipaxes) > 0:
                xform = glroutines.flip(xform, flipaxes, bounds.lo, bounds.hi)

            self.__xforms.append(xform)


    def _updateDisplayBounds(self, *args, **kwargs):
        """Overrides :meth:`.SliceCanvas._updateDisplayBounds`.

        Called on canvas resizes, display bound changes and lightbox slice
        property changes. Calculates the required bounding box that is to
        be displayed, in display coordinates.
        """

        if self.destroyed:
            return

        opts   = self.opts
        bounds = self.displayCtx.bounds
        ncols  = self.ncols
        nrows  = self.nrows
        xmin   = bounds.getLo( opts.xax)
        ymin   = bounds.getLo( opts.yax)
        xlen   = bounds.getLen(opts.xax)
        ylen   = bounds.getLen(opts.yax)

        xmax = xmin + xlen * ncols
        ymax = ymin + ylen * nrows

        log.debug('Required lightbox bounds: X: (%s, %s) Y: (%s, %s)',
                  xmin, xmax, ymin, ymax)

        width, height = self.GetSize()
        xmin, xmax, ymin, ymax = glroutines.preserveAspectRatio(
            width, height, xmin, xmax, ymin, ymax)

        opts.displayBounds[:] = (xmin, xmax, ymin, ymax)


    def _drawGridLines(self):
        """Draws grid lines between all the displayed slices."""

        if len(self.__zposes) == 0:
            return

        opts  = self.opts
        nrows = self.nrows
        ncols = self.ncols

        xlen = self.displayCtx.bounds.getLen(opts.xax)
        ylen = self.displayCtx.bounds.getLen(opts.yax)
        xmin = self.displayCtx.bounds.getLo( opts.xax)
        ymin = self.displayCtx.bounds.getLo( opts.yax)

        rowLines = np.zeros(((nrows - 1) * 2, 2), dtype=np.float32)
        colLines = np.zeros(((ncols - 1) * 2, 2), dtype=np.float32)

        rowLines[:, 1] = np.arange(
            ymin + ylen,
            ymin + ylen * nrows, ylen).repeat(2)

        rowLines[:, 0] = np.tile(
            np.array([xmin, xmin + ncols * xlen]),
            nrows - 1)

        colLines[:, 0] = np.arange(
            xmin + xlen,
            xmin + xlen * ncols, xlen).repeat(2)

        colLines[:, 1] = np.tile(
            np.array([ymin, ymin + ylen * nrows]),
            ncols - 1)

        colour = (0.3, 0.9, 1.0, 0.8)

        for lines in (rowLines, colLines):
            for i in range(0, len(lines), 2):
                self.getAnnotations().line(*lines[i],
                                           *lines[i + 1],
                                           colour=colour,
                                           width=2)


    def _drawSliceHighlight(self):
        """Draws a box around the slice which contains the current cursor
        location.
        """

        if len(self.__zposes) == 0:
            return

        opts              = self.opts
        bounds            = self.displayCtx.bounds
        xlen              = bounds.getLen(opts.xax)
        ylen              = bounds.getLen(opts.yax)
        xmin              = bounds.getLo( opts.xax)
        ymin              = bounds.getLo( opts.yax)
        sliceno, row, col = self.gridPosition()

        # don't draw the cursor if it
        # is on a non-existent slice
        if not (0 <= sliceno < self.nslices):
            return

        # in GL space, the top row is actually the bottom row
        row = self.nrows - row - 1

        self.getAnnotations().rect(xmin + xlen * col,
                                   ymin + ylen * row,
                                   xlen,
                                   ylen,
                                   filled=False,
                                   colour=(1, 0, 0),
                                   width=2)


    def _drawCursor(self):
        """Draws a cursor at the current canvas position (the
        :attr:`.SliceCanvas.pos` property).
        """

        opts              = self.opts
        bounds            = self.displayCtx.bounds
        nrows             = self.nrows
        xlen              = bounds.getLen(opts.xax)
        ylen              = bounds.getLen(opts.yax)
        xmin              = bounds.getLo( opts.xax)
        ymin              = bounds.getLo( opts.yax)
        sliceno, row, col = self.gridPosition()

        # don't draw the cursor if it
        # is on a non-existent slice
        if not (0 <= sliceno < self.nslices):
            return

        # in GL space, the top row is actually the bottom row
        row = nrows - row - 1

        xpos, ypos = self.worldToCanvas(opts.pos.xyz)

        xverts = np.zeros((2, 2))
        yverts = np.zeros((2, 2))

        xverts[:, 0] = xpos
        xverts[0, 1] = ymin + (row)     * ylen
        xverts[1, 1] = ymin + (row + 1) * ylen

        yverts[:, 1] = ypos
        yverts[0, 0] = xmin + (col)     * xlen
        yverts[1, 0] = xmin + (col + 1) * xlen

        annot  = self.getAnnotations()
        kwargs = {
            'colour'     : opts.cursorColour,
            'lineWidth'  : opts.cursorWidth
        }

        annot.line(*xverts[0], *xverts[1], **kwargs)
        annot.line(*yverts[0], *yverts[1], **kwargs)


    def _draw(self, *a):
        """Draws the current scene to the canvas. """

        if self.destroyed:
            return

        width, height = self.GetScaledSize()
        opts          = self.opts
        dctx          = self.displayCtx
        axes          = (opts.xax, opts.yax, opts.zax)

        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        gl.glViewport(0, 0, width, height)
        glroutines.clear(opts.bgColour)

        overlays, globjs = self._getGLObjects()

        # See comment in SliceCanvas._draw
        # regarding this test
        if any(not g.ready() for g in globjs):
            return

        self._setViewport(invertX=False, invertY=False)
        if self.projectionMatrix is None:
            return

        # set up off-screen texture as rendering target
        if opts.renderMode == 'onscreen':
            renderTarget = self
        else:
            log.debug('Rendering to off-screen texture')

            renderTarget = self._offscreenRenderTexture

            lo = [None] * 3
            hi = [None] * 3

            lo[opts.xax], hi[opts.xax] = opts.displayBounds.x
            lo[opts.yax], hi[opts.yax] = opts.displayBounds.y
            lo[opts.zax]               = dctx.bounds.getLo(opts.zax)
            hi[opts.zax]               = dctx.bounds.getHi(opts.zax)

            renderTarget.bindAsRenderTarget()
            renderTarget.setRenderViewport(opts.xax, opts.yax, lo, hi)
            glroutines.clear((0, 0, 0, 0))

        zposes = self.__zposes
        xforms = self.__xforms

        # Draw all the slices for all the overlays.
        for overlay, globj in zip(overlays, globjs):

            display = self.displayCtx.getDisplay(overlay)
            globj   = self._glObjects.get(overlay, None)

            if not display.enabled:
                continue

            log.debug('Drawing %s slices for overlay %s', len(zposes), overlay)
            globj.preDraw()
            globj.drawAll(renderTarget, axes, zposes, xforms)
            globj.postDraw()

        # draw off-screen texture to screen
        if opts.renderMode == 'offscreen':
            renderTarget.unbindAsRenderTarget()
            renderTarget.restoreViewport()
            glroutines.clear(opts.bgColour)
            renderTarget.drawOnBounds(
                0,
                opts.displayBounds.xlo,
                opts.displayBounds.xhi,
                opts.displayBounds.ylo,
                opts.displayBounds.yHi,
                opts.xax,
                opts.yax,
                self.mvpMatrix)

        if len(self.overlayList) > 0:
            if opts.showCursor:     self._drawCursor()
            if opts.showGridLines:  self._drawGridLines()
            if opts.highlightSlice: self._drawSliceHighlight()

        if opts.showLocation:
            self.__labelMgr.refreshLabels()

        self.getAnnotations().draw2D(opts.pos[opts.zax], axes)
