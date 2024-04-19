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

        :arg displayCtx:   The :class:`.DisplayContext` managing the
                           :class:`.LightBoxCanvas`.

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
        # We force the display space to the
        # image, so the voxel Z axis will
        # correspond to the display Z axis.
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


    def _onPerformanceChange(self, *a):
        """Overrides :meth:`.SceneOpts._onPerformanceChange`. Changes the value
        of the :attr:`renderMode` property according to the performance setting.
        """

        if   self.performance == 3: self.renderMode = 'onscreen'
        elif self.performance == 2: self.renderMode = 'offscreen'

        log.debug('Performance settings changed: '
                  'renderMode=%s', self.renderMode)
