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
    ncols          = copy.copy(canvasopts.LightBoxCanvasOpts.ncols)
    zrange         = copy.copy(canvasopts.LightBoxCanvasOpts.zrange)
    showGridLines  = copy.copy(canvasopts.LightBoxCanvasOpts.showGridLines)
    highlightSlice = copy.copy(canvasopts.LightBoxCanvasOpts.highlightSlice)

    # SliceCanvas has (prerender, offscreen, onscreen)
    # performance settings, but LightBoxCanvas only has
    # (offscreen, onscreen) settings.
    performance = props.Choice((2, 3), default=3, allowStr=True,
                               alternates=[[1, '1'], []])


    def __init__(self, *args, **kwargs):
        """Create a ``LightBoxOpts`` instance. All arguments are passed
        through to the :class:`.SceneOpts` constructor.

        The :attr:`.SceneOpts.zoom` attribute is modified, as
        :class:`LightBoxPanel` uses it slightly differently to the
        :class:`OrthoPanel`.
        """
        sceneopts.SceneOpts.__init__(self, *args, **kwargs)
        self.zax = 2
        self.setAttribute('zax',  'default', 2)
        self.setAttribute('zoom', 'minval',  10)
        self.setAttribute('zoom', 'maxval',  1000)


    def _onPerformanceChange(self, *a):
        """Overrides :meth:`.SceneOpts._onPerformanceChange`. Changes the
        value of the :attr:`renderMode` and :attr:`highDpi` properties
        according to the performance setting.
        """

        if   self.performance == 3: self.renderMode = 'onscreen'
        elif self.performance == 2: self.renderMode = 'offscreen'

        self.highDpi = self.performance == 3 and self.highDpi

        log.debug('Performance settings changed: '
                  'renderMode=%s', self.renderMode)
