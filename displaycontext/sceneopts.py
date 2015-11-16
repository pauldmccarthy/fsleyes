#!/usr/bin/env python
#
# sceneopts.py - Provides the SceneOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.SceneOpts` class, which contains display
settings used by :class:`.CanvasPanel` instances.
"""


import copy
import logging

import props

import canvasopts


log = logging.getLogger(__name__)


class SceneOpts(props.HasProperties):
    """The ``SceneOpts`` class defines settings which are used by
    :class:`.CanvasPanel` instances.

    Several of the properties of the ``SceneOpts`` class are defined in the
    :class:`.SliceCanvasOpts` class, so see its documentation for more
    details.
    """

    
    showCursor      = copy.copy(canvasopts.SliceCanvasOpts.showCursor)
    zoom            = copy.copy(canvasopts.SliceCanvasOpts.zoom)
    bgColour        = copy.copy(canvasopts.SliceCanvasOpts.bgColour)
    cursorColour    = copy.copy(canvasopts.SliceCanvasOpts.cursorColour)
    resolutionLimit = copy.copy(canvasopts.SliceCanvasOpts.resolutionLimit)
    renderMode      = copy.copy(canvasopts.SliceCanvasOpts.renderMode)

    
    showColourBar = props.Boolean(default=False)
    """If ``True``, and it is possible to do so, a colour bar is shown on
    the scene.
    """

    
    colourBarLocation  = props.Choice(('top', 'bottom', 'left', 'right'))
    """This property controls the location of the colour bar, if it is being
    shown.
    """

    
    colourBarLabelSide = props.Choice(('top-left', 'bottom-right'))
    """This property controls the location of the colour bar labels, relative
    to the colour bar, if it is being shown.
    """ 

    
    performance = props.Choice((1, 2, 3, 4), default=4)
    """User controllable performance setting.

    This property is linked to the :attr:`renderMode` and
    :attr:`resolutionLimit` properties. Setting this property to a low value
    will result in faster rendering time, at the cost of increased memory
    usage and poorer rendering quality.

    See the :meth:`__onPerformanceChange` method.
    """


    def __init__(self):
        """Create a ``SceneOpts`` instance.

        This method simply links the :attr:`performance` property to the
        :attr:`renderMode` and :attr:`resolutionLimit` properties.
        """
        
        name = '{}_{}'.format(type(self).__name__, id(self))
        self.addListener('performance', name, self._onPerformanceChange)
        
        self._onPerformanceChange()

        
    def _onPerformanceChange(self, *a):
        """Called when the :attr:`performance` property changes.

        This method must be overridden by sub-classes to change the values of
        the :attr:`renderMode` and :attr:`resolutionLimit` properties
        according to the new performance setting.
        """        
        raise NotImplementedError('The _onPerformanceChange method must'
                                  'be implemented by sub-classes')
