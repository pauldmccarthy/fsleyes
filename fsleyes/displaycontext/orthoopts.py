#!/usr/bin/env python
#
# orthoopts.py - The OrthoOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoOpts` class, which contains display
settings used by the :class:`.OrthoPanel` class.
"""


import logging
import copy

import fsleyes_props      as props

from . import sceneopts
from . import canvasopts


log = logging.getLogger(__name__)


class OrthoOpts(sceneopts.SceneOpts):
    """The ``OrthoOpts`` class is used by :class:`.OrthoPanel` instances to
    manage their display settings.


    .. note:: While the ``OrthoOpts`` class has :attr:`xzoom`, :attr:`yzoom`,
              and :attr:`zzoom`, properties which control the zoom levels on
              each canvas independently, ``OrthoOpts`` class also inherits a
              ``zoom`` property from the :class:`.SceneOpts` class. This
              *global* zoom property can be used to adjust all canvas zoom
              levels simultaneously.
    """


    cursorGap = copy.copy(canvasopts.SliceCanvasOpts.cursorGap)


    showXCanvas = props.Boolean(default=True)
    """Toggles display of the X canvas."""


    showYCanvas = props.Boolean(default=True)
    """Toggles display of the Y canvas."""


    showZCanvas = props.Boolean(default=True)
    """Toggles display of the Z canvas."""


    showLabels = props.Boolean(default=True)
    """If ``True``, labels showing anatomical orientation are displayed on
    each of the canvases.
    """


    layout = props.Choice(('horizontal', 'vertical', 'grid'))
    """How should we lay out each of the three canvases?"""


    xzoom = copy.copy(sceneopts.SceneOpts.zoom)
    """Controls zoom on the X canvas."""


    yzoom = copy.copy(sceneopts.SceneOpts.zoom)
    """Controls zoom on the Y canvas."""


    zzoom = copy.copy(sceneopts.SceneOpts.zoom)
    """Controls zoom on the Z canvas. """


    invertXHorizontal = copy.copy(canvasopts.SliceCanvasOpts.invertX)
    """Invert the X canvas along the horizontal axis. """


    invertXVertical = copy.copy(canvasopts.SliceCanvasOpts.invertY)
    """Invert the X canvas along the vertical axis. """


    invertYHorizontal = copy.copy(canvasopts.SliceCanvasOpts.invertX)
    """Invert the Y canvas along the horizontal axis. """


    invertYVertical = copy.copy(canvasopts.SliceCanvasOpts.invertY)
    """Invert the Y canvas along the vertical axis. """


    invertZHorizontal = copy.copy(canvasopts.SliceCanvasOpts.invertX)
    """Invert the Z canvas along the horizontal axis. """


    invertZVertical = copy.copy(canvasopts.SliceCanvasOpts.invertY)
    """Invert the Z canvas along the vertical axis. """


    def __init__(self, *args, **kwargs):
        """Create an ``OrthoOpts`` instance. All arguments are passed
        through to the :class:`.SceneOpts` constructor.

        This method sets up a binding from the :attr:`.SceneOpts.zoom`
        property to the :attr:`xzoom`, :attr:`yzoom`, and :attr:`zzoom`
        properties - see :meth:`__onZoom`.
        """
        sceneopts.SceneOpts.__init__(self, *args, **kwargs)

        name = '{}_{}'.format(type(self).__name__, id(self))

        self.addListener('zoom', name, self.__onZoom)


    def __onZoom(self, *a):
        """Called when the :attr:`.SceneOpts.zoom` property changes.

        Propagates the change to the :attr:`xzoom`, :attr:`yzoom`, and
        :attr:`zzoom` properties.
        """
        self.xzoom = self.zoom
        self.yzoom = self.zoom
        self.zzoom = self.zoom


    def _onPerformanceChange(self, *a):
        """Overrides :meth:`.SceneOpts._onPerformanceChange`. Changes the
        value of the :attr:`renderMode` and :attr:`highDpi` properties
        according to the performance setting.
        """

        if   self.performance == 3: self.renderMode = 'onscreen'
        elif self.performance == 2: self.renderMode = 'offscreen'
        elif self.performance == 1: self.renderMode = 'prerender'

        self.highDpi = self.performance == 3 and self.highDpi

        log.debug('Performance settings changed: '
                  'renderMode={}'.format(self.renderMode))
