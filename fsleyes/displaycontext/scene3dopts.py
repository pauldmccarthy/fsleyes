#!/usr/bin/env python
#
# scene3dopts.py - The Scene3DOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Scene3DOpts` class, which is used
by :class:`.Scene3DPanel` instances for managing their display settings.
"""


import copy


from . import sceneopts
from . import canvasopts


class Scene3DOpts(sceneopts.SceneOpts):
    """The ``Scene3DOpts`` class contains display settings for the
    :class:`.Scene3DPanel` class.

    All of the properties in the ``Scene3DOpts`` class are defined in the
    :class:`.Scene3DCanvasOpts` class - see its documentation for more
    details.
    """


    showLegend = copy.copy(canvasopts.Scene3DCanvasOpts.showLegend)
    centre     = copy.copy(canvasopts.Scene3DCanvasOpts.centre)
    rotation   = copy.copy(canvasopts.Scene3DCanvasOpts.rotation)



    def __init__(self, *args, **kwargs):
        """Create a ``Scene3DCanvasOpts`` instance. All arguments are passed
        through to the :class:`.SceneOpts` constructor.

        The :attr:`.SceneOpts.zoom` attribute is modified slightly.
        """
        sceneopts.SceneOpts.__init__(self, *args, **kwargs)
        self.setConstraint('zoom', 'minval',   1)
        self.setConstraint('zoom', 'default',  75)
        self.setConstraint('zoom', 'maxval',   5000)
        self.zoom = 75


    def _onPerformanceChange(self, *a):
        """Overrides :meth:`.SceneOpts._onPerformanceChange`. Currently
        does nothing.
        """
        pass
