#!/usr/bin/env python
#
# lightboxopts.py - The LightBoxOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxOpts` class, which is used
by :class:`.LightBoxPanel` instances for managing their display settings.
"""


import logging
import copy

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

    sliceSpacing   = copy.copy(canvasopts.LightBoxCanvasOpts.sliceSpacing)
    zax            = copy.copy(canvasopts.LightBoxCanvasOpts.zax)
    zrange         = copy.copy(canvasopts.LightBoxCanvasOpts.zrange)
    nrows          = copy.copy(canvasopts.LightBoxCanvasOpts.nrows)
    ncols          = copy.copy(canvasopts.LightBoxCanvasOpts.ncols)
    showGridLines  = copy.copy(canvasopts.LightBoxCanvasOpts.showGridLines)
    highlightSlice = copy.copy(canvasopts.LightBoxCanvasOpts.highlightSlice)
    showLocation   = copy.copy(canvasopts.LightBoxCanvasOpts.showLocation)

    # SliceCanvas has (prerender, offscreen, onscreen)
    # performance settings, but LightBoxCanvas only has
    # (offscreen, onscreen) settings.
    performance = props.Choice((2, 3), default=3, allowStr=True,
                               alternates=[[1, '1'], []])


    def _onPerformanceChange(self, *a):
        """Overrides :meth:`.SceneOpts._onPerformanceChange`. Changes the value
        of the :attr:`renderMode` property according to the performance setting.
        """

        if   self.performance == 3: self.renderMode = 'onscreen'
        elif self.performance == 2: self.renderMode = 'offscreen'

        log.debug('Performance settings changed: '
                  'renderMode=%s', self.renderMode)
