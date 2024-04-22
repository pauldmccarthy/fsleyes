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

import fsl.transform.affine              as affine
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
    slice with the maximum Z value translated to the bottom right (this
    mapping can be inverted via the :attr:`.LightBoxCanvasOpts.reverseSlices`
    property).

    A suitable number of rows and columns are automatically calculated
    whenever the canvas size is changed, or any :class:`.LightBoxCanvasOpts`
    properties change.

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


    def __init__(self, overlayList, displayCtx, zax=None, freezeOpts=False):
        """Create a ``LightBoxCanvas`` object.

        :arg overlayList: An :class:`.OverlayList` object which contains a
                          list of overlays to be displayed.

        :arg displayCtx: A :class:`.DisplayContext` object which defines how
                         that overlay list is to be displayed.

        :arg zax:        Display coordinate system axis to be used as the
                         'depth' axis. Can be changed via the
                         :attr:`.SliceCanvas.zax` property.

        :arg freezeOpts: Defaults to ``False``. If ``True``, the properties
                         of the internal :class:`.LightBoxCanvasOpts` instance
                         will not be adjusted. This is used in off-screen
                         rendering
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
        opts.ilisten('sliceOverlap',   self.name, self._slicePropsChanged)
        opts.ilisten('sampleSlices',   self.name, self._slicePropsChanged)
        opts.ilisten('reverseSlices',  self.name, self._slicePropsChanged)
        opts.ilisten('zrange',         self.name, self._slicePropsChanged)
        opts.ilisten('nrows',          self.name, self._slicePropsChanged)
        opts.ilisten('ncols',          self.name, self._slicePropsChanged)
        opts.ilisten('invertX',        self.name, self._slicePropsChanged,
                     overwrite=True)
        opts.ilisten('invertY',        self.name, self._slicePropsChanged,
                     overwrite=True)
        opts. listen('showGridLines',  self.name, self.Refresh)
        opts. listen('highlightSlice', self.name, self.Refresh)
        opts. listen('labelSpace',     self.name, self.Refresh)
        opts. listen('labelSize',      self.name, self.Refresh)
        opts. listen('fgColour',       self.name, self.Refresh)
        opts. listen('reverseOverlap', self.name, self.Refresh)

        # Make sure that slice settings are initialised
        # to sensible values. If freezeOpts is true, they
        # will not be re-initialised when e.g. overlays
        # are added.
        self.__freezeOpts = False
        self._adjustSliceProps(True, True)
        self.__freezeOpts = freezeOpts


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
        opts.remove('sliceOverlap',   name)
        opts.remove('sampleSlices',   name)
        opts.remove('reverseOverlap', name)
        opts.remove('reverseSlices',  name)
        opts.remove('zrange',         name)
        opts.remove('nrows',          name)
        opts.remove('ncols',          name)
        opts.remove('showGridLines',  name)
        opts.remove('highlightSlice', name)
        opts.remove('labelSpace',     name)

        if self._offscreenRenderTexture is not None:
            self._offscreenRenderTexture.destroy()

        self.__labelMgr.destroy()
        self.__labelMgr = None

        slicecanvas.SliceCanvas.destroy(self)


    @property
    def gridParams(self):
        """Return an object which contains properties describing the current
        slice grid layout.
        """

        class Params:
            pass

        opts        = self.opts
        bounds      = self.displayCtx.bounds
        overlap     = opts.sliceOverlap / 100
        nrows       = self.nrows
        ncols       = self.ncols
        p           = Params()
        p.gridxmin  = bounds.getLo( opts.xax)
        p.gridymin  = bounds.getLo( opts.yax)
        p.slicexlen = bounds.getLen(opts.xax)
        p.sliceylen = bounds.getLen(opts.yax)
        p.xoffset   = p.slicexlen - p.slicexlen * overlap
        p.yoffset   = p.sliceylen - p.sliceylen * overlap
        p.gridxlen  = (ncols - 1) * p.xoffset + p.slicexlen
        p.gridylen  = (nrows - 1) * p.yoffset + p.sliceylen
        p.gridxmax  = p.gridxmin + p.gridxlen
        p.gridymax  = p.gridymin + p.gridylen

        return p


    def gridPosition(self, pos=None):
        """Returns the slice, row, and column index of the current display
        location (from the :attr:`.SliceCanvas.pos` attribute).
        """

        opts    = self.opts
        bounds  = self.displayCtx.bounds
        ncols   = self.ncols
        nslices = len(self.__zposes)
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

        if opts.reverseSlices:
            sliceno = nslices - sliceno - 1

        row = int(np.floor(sliceno / ncols))
        col = int(np.floor(sliceno % ncols))

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
        grid        = self.gridParams
        _, row, col = self.gridPosition(pos)

        if row < 0           or \
           col < 0           or \
           row >= self.nrows or \
           col >= self.ncols:
            return None

        xmin = grid.gridxmin
        ymin = grid.gridymin
        xlen = grid.slicexlen
        ylen = grid.sliceylen
        xoff = grid.xoffset
        yoff = grid.yoffset

        if opts.invertX: xpos = xmin + xlen - (xpos - xmin)
        if opts.invertY: ypos = ymin + ylen - (ypos - ymin)

        xpos = xpos + xoff * col
        ypos = ypos + yoff * (nrows - row - 1)

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
        grid    = self.gridParams
        ncols   = self.ncols
        nrows   = self.nrows

        screenPos = slicecanvas.SliceCanvas.canvasToWorld(
            self, xpos, ypos, invertX=False, invertY=False)

        if screenPos is None:
            return None

        xmin      = grid.gridxmin
        ymin      = grid.gridymin
        xmax      = grid.gridxmax
        ymax      = grid.gridymax
        slicexlen = grid.slicexlen
        sliceylen = grid.sliceylen
        gridxlen  = grid.gridxlen
        gridylen  = grid.gridylen

        # The [ymin, ymax] on the canvas is at [bottom,
        # top], but in the slice grid we denote the top
        # row as 0.  So we calculate the row index from
        # an inverted Y coordinate.
        screenx    = screenPos[opts.xax]
        screeny    = screenPos[opts.yax]
        invscreenx = xmin + gridxlen - screenx + xmin
        invscreeny = ymin + gridylen - screeny + ymin

        # Convert coordinates into row/column indices
        # using the x/y offsets - these will be equal
        # to slice x/y lengths when sliceOverlap is 0.
        #
        # However, if we are drawing slices in reverse
        # order (so that lower slices are drawn on top
        # of higher slices), we calculate the
        # row/column indices from inverted x/y
        # coordinates, so that coordinates in overlapping
        # areas will be assigned to the lower slice.
        if opts.reverseOverlap:
            col = np.floor((invscreenx - xmin) / grid.xoffset)
            row = np.floor((screeny    - ymin) / grid.yoffset)
            col = ncols - col - 1
            row = nrows - row - 1
        else:
            col = np.floor((screenx    - xmin) / grid.xoffset)
            row = np.floor((invscreeny - ymin) / grid.yoffset)

        # If sliceOverlap > 0, x/y offset will be less
        # than slice x/y lengths, so we need to ensure
        # that the indices are clamped to the max.
        col     = int(np.clip(col, 0, ncols - 1))
        row     = int(np.clip(row, 0, nrows - 1))
        sliceno = row * ncols + col

        if screenx <  xmin or \
           screenx >  xmax or \
           screeny <  ymin or \
           screeny >  ymax or \
           sliceno >= len(self.__zposes):
            return None

        xpos = screenx -          col      * grid.xoffset
        ypos = screeny - (nrows - row - 1) * grid.yoffset
        zpos = self.__zposes[sliceno]

        if opts.invertX: xpos = slicexlen - (xpos - xmin) + xmin
        if opts.invertY: ypos = sliceylen - (ypos - ymin) + ymin

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
        rots = affine.decompose(dopts.getTransform('voxel', 'display'))[2]
        rots = np.array(rots)

        # image to display transform comprises
        # 90 degree rotations, so image data
        # grid is is orthogonal to display
        # coord system. Base slice spacing on
        # z axis voxel spacing.
        if np.all(np.isclose(rots % (np.pi / 2), 0)):

            # Get the voxel z axis that corresponds
            # to the display z axis
            axmap = overlay.axisMapping(dopts.getTransform('display', 'voxel'))
            zax   = abs(axmap[copts.zax]) - 1
            return 1 / overlay.shape[zax]

        # image may be rotated w.r.t.
        # display coordinate system -
        # return smallest spacing that
        # will cover all voxel axes
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


    def _displaySpaceChanged(self):
        """Overrides :meth:`.SliceCanvas._displaySpaceChanged`. Update slice
        spacing properties, and calls the super implementation.
        """
        self._adjustSliceProps(True, True)
        super()._displaySpaceChanged()


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
        if len(self.overlayList) == 0:
            return
        if self.__freezeOpts:
            return
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
        start  = opts.startslice
        end    = start + nslices
        zposes = zmin + opts.slices[start:end] * zlen

        if opts.reverseSlices:
            zposes = zposes[::-1]

        self.__zposes = zposes
        self.__xforms = []
        self.__nrows  = nrows
        self.__ncols  = ncols

        # record start/end slice locations and
        # spacing in absolute/display coordinates
        # rather than relative proportions, as
        # the _overlayListChanged method may need
        # to restore them.
        grid           = self.gridParams
        spacing        = zlen * opts.sliceSpacing
        zlo, zhi       = opts.normzrange
        zlo            = zmin + zlo * zlen
        zhi            = zmin + zhi * zlen
        self.__zbounds = [zlo, zhi, spacing]

        for sliceno in range(len(self.__zposes)):

            row = int(np.floor(sliceno / ncols))
            col = int(np.floor(sliceno % ncols))

            xform              = np.eye(4, dtype=np.float32)
            xform[opts.xax, 3] = grid.xoffset * col
            xform[opts.yax, 3] = grid.yoffset * (nrows - row - 1)
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

        opts = self.opts
        grid = self.gridParams
        xmin = grid.gridxmin
        ymin = grid.gridymin
        xmax = grid.gridxmax
        ymax = grid.gridymax

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
        grid  = self.gridParams
        xlen  = grid.slicexlen
        ylen  = grid.sliceylen
        xoff  = grid.xoffset
        yoff  = grid.yoffset
        xmin  = grid.gridxmin
        ymin  = grid.gridymin
        xmax  = grid.gridxmax
        ymax  = grid.gridymax

        # no slice overlap
        if opts.sliceOverlap == 0:
            rowLines       = np.zeros(((nrows - 1) * 2, 2), dtype=np.float32)
            colLines       = np.zeros(((ncols - 1) * 2, 2), dtype=np.float32)
            colLines[:, 0] = np.arange(xmin + xlen, xmax, xlen).repeat(2)
            rowLines[:, 1] = np.arange(ymin + ylen, ymax, ylen).repeat(2)
            colLines[:, 1] = np.tile([ymin, ymax], ncols - 1)
            rowLines[:, 0] = np.tile([xmin, xmax], nrows - 1)

        else:
            rowLines = np.zeros(((nrows - 1) * 4, 2), dtype=np.float32)
            colLines = np.zeros(((ncols - 1) * 4, 2), dtype=np.float32)

            nrowpairs = (nrows - 1) * 2
            ncolpairs = (ncols - 1) * 2

            # Vertices for lines at bottom/left of each slice
            rowLines[:nrowpairs, 1] = ymin + yoff + \
                yoff * np.arange(nrowpairs / 2).repeat(2)
            colLines[:ncolpairs, 0] = xmin + xoff + \
                xoff * np.arange(ncolpairs / 2).repeat(2)

            # Vertices for lines at top/right of each slice
            rowLines[nrowpairs:, 1] = rowLines[:nrowpairs, 1] + (ylen - yoff)
            colLines[ncolpairs:, 0] = colLines[:ncolpairs, 0] + (xlen - xoff)

            # Row x/col y coords
            rowLines[:, 0] = np.tile([xmin, xmax], nrowpairs)
            colLines[:, 1] = np.tile([ymin, ymax], ncolpairs)

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

        grid              = self.gridParams
        xlen              = grid.slicexlen
        ylen              = grid.sliceylen
        xoff              = grid.xoffset
        yoff              = grid.yoffset
        xmin              = grid.gridxmin
        ymin              = grid.gridymin
        sliceno, row, col = self.gridPosition()

        # don't draw the cursor if it
        # is on a non-existent slice
        if not (0 <= sliceno < self.nslices):
            return

        # in GL space, the top row is actually the bottom row
        row = self.nrows - row - 1

        self.getAnnotations().rect(xmin + xoff * col,
                                   ymin + yoff * row,
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
        grid              = self.gridParams
        nrows             = self.nrows
        xlen              = grid.slicexlen
        ylen              = grid.sliceylen
        xoff              = grid.xoffset
        yoff              = grid.yoffset
        xmin              = grid.gridxmin
        ymin              = grid.gridymin
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
        xverts[0, 1] = ymin + (row) * yoff
        xverts[1, 1] = xverts[0, 1] + ylen

        yverts[:, 1] = ypos
        yverts[0, 0] = xmin + (col) * xoff
        yverts[1, 0] = yverts[0, 0] + xlen

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

        if opts.reverseOverlap:
            zposes = list(reversed(zposes))
            xforms = list(reversed(xforms))

        # Draw all the slices for all the overlays.
        # If there is no overlap (or there is only
        # one overlay), we can draw all the slices
        # for each overlay in a single call.
        if not ((opts.sliceOverlap > 0) and (len(overlays) > 1)):
            for overlay, globj in zip(overlays, globjs):
                log.debug('Drawing %s slices for overlay %s',
                          len(zposes), overlay)
                globj.preDraw()
                globj.drawAll(renderTarget, axes, zposes, xforms)
                globj.postDraw()

        # Otherwise, we have to draw all overlays
        # one slice at a time, to ensure that the
        # slices overlap properly.
        else:
            for zpos, xform in zip(zposes, xforms):
                for overlay, globj in zip(overlays, globjs):
                    log.debug('Drawing slice at %s for overlay %s',
                              zpos, overlay)
                    globj.preDraw()
                    globj.draw2D(renderTarget, zpos, axes, xform)
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

        self.__labelMgr.refreshLabels()
        self.getAnnotations().draw2D(opts.pos[opts.zax], axes)
