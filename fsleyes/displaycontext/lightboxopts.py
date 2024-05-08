#!/usr/bin/env python
#
# lightboxopts.py - The LightBoxOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxOpts` class, which is used
by :class:`.LightBoxPanel` instances for managing their display settings.
"""


import           logging
from copy import copy

import numpy as np

import fsleyes_props as props

from . import sceneopts
from . import canvasopts


log = logging.getLogger(__name__)


class LightBoxOpts(sceneopts.SceneOpts):
    """The ``LightBoxOpts`` class contains display settings for the
    :class:`.LightBoxPanel` class.

    All of the properties in the ``LightBoxOpts`` class are defined in the
    :class:`.LightBoxCanvasOpts` class - see its documentation for more
    details.
    """

    sliceSpacing   = copy(canvasopts.LightBoxCanvasOpts.sliceSpacing)
    sliceOverlap   = copy(canvasopts.LightBoxCanvasOpts.sliceOverlap)
    reverseOverlap = copy(canvasopts.LightBoxCanvasOpts.reverseOverlap)
    reverseSlices  = copy(canvasopts.LightBoxCanvasOpts.reverseSlices)
    zax            = copy(canvasopts.LightBoxCanvasOpts.zax)
    zrange         = copy(canvasopts.LightBoxCanvasOpts.zrange)
    nrows          = copy(canvasopts.LightBoxCanvasOpts.nrows)
    ncols          = copy(canvasopts.LightBoxCanvasOpts.ncols)
    showGridLines  = copy(canvasopts.LightBoxCanvasOpts.showGridLines)
    highlightSlice = copy(canvasopts.LightBoxCanvasOpts.highlightSlice)
    labelSpace     = copy(canvasopts.LightBoxCanvasOpts.labelSpace)
    sampleSlices   = copy(canvasopts.LightBoxCanvasOpts.sampleSlices)

    # SliceCanvas has (prerender, offscreen, onscreen)
    # performance settings, but LightBoxCanvas only has
    # (offscreen, onscreen) settings.
    performance = props.Choice((2, 3), default=3, allowStr=True,
                               alternates=[[1, '1'], []])


    def setSlicesFromVoxels(self, image, sliceStart, sliceEnd, sliceSpacing):
        """Sets the :attr:`zrange` and :attr:`sliceSpacing` properties
        in terms of voxel coordinates with respect to the given ``image``.

        This method assumes that:
          - the :attr:`.DisplayContext.displaySpace` is set to the ``image``
            (or to a compatible image)
          - The :attr:`sampleSlices` property is set to ``'start'``.

        :arg image:        The :class:`.Nifti` instance for which the
                           ``start``/``end``/`spacing`` values are defined

        :arg sliceStart:   Start voxel

        :arg sliceEnd:     End voxel

        :arg sliceSpacing: Spacing in voxels
        """

        dctx = self.panel.displayCtx
        zax  = self.zax
        opts = dctx.getOpts(image)

        # Transform start/end slice indices
        # into display coordinate system.
        # We assume the display space is the
        # image, so the voxel Z axis will
        # correspond to the display Z axis.
        # The transformed start/end locations
        # should correspond to voxel centres.
        start      = [0] * 3
        end        = [0] * 3
        start[zax] = sliceStart
        end[  zax] = sliceEnd + 1
        start, end = opts.transformCoords([start, end], 'voxel', 'display')
        start      = start[zax]
        end        = end[  zax]

        # Just in case there is a L/R flip
        start, end = sorted((start, end))

        # Calculate slice spacing - the
        # display space should be the image,
        # so we can just use pixdims to
        # normalise the spacing value w.r.t.
        # the display coordinate system
        spacing = sliceSpacing * image.pixdim[zax]

        # Normalise start/end locations to
        # [0, 1], with respect to the display
        # coordinate system bounding box
        zmin    = dctx.bounds.getLo(zax)
        zlen    = dctx.bounds.getLen(zax)
        start   = (start - zmin) / zlen
        end     = (end   - zmin) / zlen
        spacing = spacing        / zlen

        # Update lightbox settings
        self.zrange       = [start, end]
        self.sliceSpacing = spacing


    def getSlicesAsVoxels(self, image):
        """Inverse of :meth:`setSlicesFromVoxels`. Calculates and returns
        the current :attr:`zrange` and :attr:`sliceSpacing` in terms of
        voxel coordinates with respect to the given image.
        """

        dctx     = self.panel.displayCtx
        opts     = dctx.getOpts(image)
        zax      = self.zax
        zlo, zhi = self.zrange
        spacing  = self.sliceSpacing

        # zhi may have been clipped at 1.0, so
        # round it up to the centre of the last
        # slice (we are working in the [0, 1]
        # slice coordinate system here)
        if zhi >= 1:
            zhi = 1 + 0.5 / image.shape[zax]

        # Transform zrange and sliceSpacing from
        # [0, 1] into coordinates relative to the
        # display coordinate system bounding box
        zmin     = dctx.bounds.getLo(zax)
        zlen     = dctx.bounds.getLen(zax)
        spacing  = spacing    * zlen
        zlo      = zmin + zlo * zlen
        zhi      = zmin + zhi * zlen

        # Transform zrange/sliceSpacing into voxel
        # coordinates w.r.t. the given image. We
        # assume here that the display space is
        # set to this image.
        start      = [0] * 3
        end        = [0] * 3
        start[zax] = zlo
        end[  zax] = zhi
        start, end = opts.transformCoords([start, end], 'display', 'voxel')
        start, end = sorted((start[zax], end[zax]))
        spacing    = spacing / image.pixdim[zax]

        start   = max((round(start),   0))
        end     = min((round(end - 1), image.shape[zax]))
        spacing = max((round(spacing), 1))

        return start, end, spacing


    def _onPerformanceChange(self, *a):
        """Overrides :meth:`.SceneOpts._onPerformanceChange`. Changes the value
        of the :attr:`renderMode` property according to the performance setting.
        """

        if   self.performance == 3: self.renderMode = 'onscreen'
        elif self.performance == 2: self.renderMode = 'offscreen'

        log.debug('Performance settings changed: '
                  'renderMode=%s', self.renderMode)
