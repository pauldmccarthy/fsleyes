#!/usr/bin/env python
#
# lightboxcanvas.py - The LightBoxCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxCanvas` class, which is a
:class:`.SliceCanvas` that displays multiple 2D slices along a single axis
from a collection of 3D overlays.

Performance of a ``LightBoxCanvas`` instance may be controlled through the
:attr:`.SliceCanvasOpts.renderMode` property, in the same way as for the
:class:`.SliceCanvas`. However, the ``LightBoxCanvas`` handles the
``offscreen`` render mode differently to the ``SliceCanvas. Where the
``SliceCanvas`` uses a separate :class:`.GLObjectRenderTexture` for every
overlay in the :class:`.OverlayList`, the ``LightBoxCanvas`` uses a single
:class:`.RenderTexture` to render all overlays off-screen.
"""

import sys
import logging

import numpy     as np
import OpenGL.GL as gl

import fsleyes_props                     as props
import fsl.data.image                    as fslimage
import fsl.transform.affine              as affine

import fsleyes.displaycontext.canvasopts as canvasopts
import fsleyes.gl.slicecanvas            as slicecanvas
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


    The ``LightBoxCanvas`` class defines the following convenience methods (in
    addition to those defined in the ``SliceCanvas`` class):

    .. autosummary::
       :nosignatures:

       canvasToWorld
       worldToCanvas
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

        # These attributes store the Z position
        # for each slice, and affines encoding
        # vertical/horizontal offsets, which
        # position each slice on the canvas.
        self._zposes = []
        self._xforms = []

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
        opts.addListener('zrange',         self.name, self._slicePropsChanged)
        opts.addListener('showGridLines',  self.name, self.Refresh)
        opts.addListener('highlightSlice', self.name, self.Refresh)

        # Add a listener to the position so when it
        # changes we can adjust the zrange to ensure
        # the slice corresponding to the current z
        # position is visible. SliceCanvas.__init__
        # has already registered a listener, on pos,
        # with self.name - so we use a different
        # name here
        opts.addListener('pos',
                         f'{self.name}_zPosChanged',
                         self._zPosChanged)


    def destroy(self):
        """Overrides :meth:`.SliceCanvas.destroy`. Must be called when this
        ``LightBoxCanvas`` is no longer needed.

        Removes some property listeners, makes sure that the off screen
        :class:`.RenderTexture` (if one exists) is destroyed, and then calls
        the :meth:`.SliceCanvas.destroy` method.
        """

        opts = self.opts
        name = self.name

        opts.removeListener('pos',            f'{name}_zPosChanged')
        opts.removeListener('sliceSpacing',   name)
        opts.removeListener('ncols',          name)
        opts.removeListener('zrange',         name)
        opts.removeListener('showGridLines',  name)
        opts.removeListener('highlightSlice', name)

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
        ncols   = opts.ncols
        nrows   = opts.nrows
        bounds  = self.displayCtx.bounds
        xlen    = bounds.getLen(opts.xax)
        ylen    = bounds.getLen(opts.yax)
        xmin    = bounds.getLo( opts.xax)
        ymin    = bounds.getLo( opts.yax)
        zmin    = bounds.getLo( opts.zax)
        zlen    = bounds.getLen(opts.zax)
        sliceno = (zpos - zmin) / zlen - opts.zrange.xlo
        sliceno = int(np.floor(sliceno / opts.sliceSpacing))

        row = nrows - int(np.floor(sliceno / ncols)) - 1
        col =         int(np.floor(sliceno % ncols))

        if opts.invertX: xpos = xmin + xlen - (xpos - xmin)
        if opts.invertY: ypos = ymin + ylen - (ypos - ymin)

        xpos = xpos + xlen * col
        ypos = ypos + ylen * row

        return xpos, ypos


    @property
    def lightboxPosition(self):
        """Returns the slice, row, and column index of the current display
        location (from the :attr:`.SliceCanvas.pos` attribute).
        """

        opts    = self.opts
        bounds  = self.displayCtx.bounds
        ncols   = opts.ncols
        zmin    = bounds.getLo( opts.zax)
        zlen    = bounds.getLen(opts.zax)
        zpos    = opts.pos[opts.zax]
        sliceno = (zpos - zmin) / zlen - opts.zrange.xlo
        sliceno = int(np.floor(sliceno / opts.sliceSpacing))
        row     = int(np.floor(sliceno / ncols))
        col     = int(np.floor(sliceno % ncols))

        return sliceno, row, col


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
        ncols   = opts.ncols
        nrows   = opts.nrows
        nslices = opts.nslices

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
        zmin = bounds.getLo( opts.zax)
        zlen = bounds.getLen(opts.zax)

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
           sliceno >= nslices:
            return None

        xpos = screenx  -          col      * xlen
        ypos = screeny  - (nrows - row - 1) * ylen

        if opts.invertX: xpos = xlen - (xpos - xmin) + xmin
        if opts.invertY: ypos = ylen - (ypos - ymin) + ymin

        zpos = opts.zrange.xlo + (sliceno + 0.5) * opts.sliceSpacing
        zpos = zmin + zpos * zlen

        pos           = [0, 0, 0]
        pos[opts.xax] = xpos
        pos[opts.yax] = ypos
        pos[opts.zax] = zpos

        return tuple(pos)


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
        if dopts.transform in  ('id', 'pixdim', 'pixdim-flip'):
            return 1 / overlay.shape[copts.zax]
        if dopts.transform == 'affine':
            return 0.02

        # This overlay is being displayed with a
        # custrom transformation matrix  - check
        # to see what display space we're in
        displaySpace = displayCtx.displaySpace

        if isinstance(displaySpace, fslimage.Nifti) and \
           overlay is not displaySpace:
            return self.calcSliceSpacing(displaySpace)
        else:
            return 1 / max(overlay.shape[:3])


    def _overlayListChanged(self):
        """Overrides :meth:`.SliceCanvas._overlayListChanged`. Sets
        some limits on some of the :class:`.LightBoxCanvasOpts` properties
        as needed.
        """
        slicecanvas.SliceCanvas._overlayListChanged(self)

        if len(self.overlayList) == 0:
            return

        spacings = [self.calcSliceSpacing(o) for o in self.overlayList]
        spacing  = min(spacings)

        self.opts.setAttribute('sliceSpacing', 'minval',      spacing)
        self.opts.setAttribute('zrange',       'minDistance', spacing)


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
        """Overrides :meth:`.SliceCanvas._zAxisChanged`. Calls that
        method, and then resets the :attr:`sliceSpacing` and :attr:`zrange`
        properties to sensible values.
        """
        slicecanvas.SliceCanvas._zAxisChanged(self, *a)
        self._slicePropsChanged()


    def _slicePropsChanged(self, *a):
        """Called when any of the slice properties change. Regenerates slice
        locations and display bounds, and refreshes the canvas.
        """

        self._calculateSlices()
        self._zPosChanged()
        self._updateDisplayBounds()

        if log.getEffectiveLevel() == logging.DEBUG:
            opts  = self.opts
            props = [('ncols',        opts.ncols),
                     ('sliceSpacing', opts.sliceSpacing),
                     ('zrange',       opts.zrange)]

            props = '; '.join(['{}={}'.format(k, v) for k, v in props])

            log.debug('Lightbox properties changed: [%s]', props)

        self.Refresh()


    def _updateRenderTextures(self):
        """Overrides :meth:`.SliceCanvas._updateRenderTextures`. Does nothing.
        """


    def _zPosChanged(self, *a):
        """Called when the :attr:`.SliceCanvas.pos` ``z`` value changes.

        Makes sure that the corresponding slice is visible.
        """

        if len(self.overlayList) == 0:
            return

        # figure out where we are in the canvas world
        opts             = self.opts
        zax              = opts.zax
        bounds           = self.displayCtx.bounds
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
        zmin    = bounds.getLo( zax)
        zlen    = bounds.getLen(zax)
        zpos    = opts.pos[zax]
        sliceno = (zpos - zmin) / zlen - opts.zrange.xlo
        sliceno = int(np.floor(sliceno / opts.sliceSpacing))
        row     = int(np.floor(sliceno / opts.ncols))

        # and make sure that row is visible
        opts.topRow = row


    def _overlayBoundsChanged(self, *a):
        """Overrides :meth:`.SliceCanvas._overlayBoundsChanged`.

        Called when the :attr:`.DisplayContext.bounds` change. Updates the
        :attr:`zrange` min/max values.
        """

        slicecanvas.SliceCanvas._overlayBoundsChanged(self, preserveZoom=False)
        self._calculateSlices()


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
        ncols  = opts.ncols
        nrows  = opts.nrows
        xmin   = bounds.getLo( opts.xax)
        ymin   = bounds.getLo( opts.yax)
        xlen   = bounds.getLen(opts.xax)
        ylen   = bounds.getLen(opts.yax)

        xmax = xmin + xlen * ncols
        ymax = ymin + ylen * nrows

        # Save the real canvas bounds (before
        # aspect ratio adjustment)
        self._realBounds = (xmin, xmax, ymin, ymax)

        log.debug('Required lightbox bounds: X: (%s, %s) Y: (%s, %s)',
                  xmin, xmax, ymin, ymax)

        width, height = self.GetSize()
        xmin, xmax, ymin, ymax = glroutines.preserveAspectRatio(
            width, height, xmin, xmax, ymin, ymax)

        opts.displayBounds[:] = (xmin, xmax, ymin, ymax)


    def _calculateSlices(self):
        """Calculates Z positions and affine transformations for each slice.
        The transformations are used to position each slice at a row/column
        on the canvas.
        """

        opts    = self.opts
        bounds  = self.displayCtx.bounds
        ncols   = opts.ncols
        nrows   = opts.nrows
        xlen    = bounds.getLen(opts.xax)
        ylen    = bounds.getLen(opts.yax)
        zlen    = bounds.getLen(opts.zax)
        zmin    = bounds.getLo( opts.zax)
        spacing = zlen * opts.sliceSpacing
        zlo     = zmin + opts.zrange.xlo * zlen
        zhi     = zmin + opts.zrange.xhi * zlen

        self._zposes = []
        self._xforms = []

        if len(self.overlayList) == 0 or np.isclose(zlen, 0):
            return

        # calculate the locations, in display coordinates,
        # of all slices to be displayed on the canvas, and
        # calculate the X/Y transformation for each slice
        # to position it on the canvas
        self._zposes = np.arange(zlo, zhi, spacing)

        for sliceno in range(len(self._zposes)):

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

            self._xforms.append(xform)


    def _drawGridLines(self):
        """Draws grid lines between all the displayed slices."""

        if len(self._zposes) == 0:
            return

        opts  = self.opts
        nrows = opts.nrows
        ncols = opts.ncols

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

        if len(self._zposes) == 0:
            return

        opts              = self.opts
        bounds            = self.displayCtx.bounds
        xlen              = bounds.getLen(opts.xax)
        ylen              = bounds.getLen(opts.yax)
        xmin              = bounds.getLo( opts.xax)
        ymin              = bounds.getLo( opts.yax)
        sliceno, row, col = self.lightboxPosition

        # don't draw the cursor if it
        # is on a non-existent slice
        if not (0 <= sliceno < opts.nslices):
            return

        # in GL space, the top row is actually the bottom row
        row = opts.nrows - row - 1

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
        nrows             = opts.nrows
        xlen              = bounds.getLen(opts.xax)
        ylen              = bounds.getLen(opts.yax)
        xmin              = bounds.getLo( opts.xax)
        ymin              = bounds.getLo( opts.yax)
        sliceno, row, col = self.lightboxPosition

        # don't draw the cursor if it
        # is on a non-existent slice
        if not (0 <= sliceno < opts.nslices):
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

        zposes = self._zposes
        xforms = self._xforms

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

        self.getAnnotations().draw2D(opts.pos[opts.zax], axes)
