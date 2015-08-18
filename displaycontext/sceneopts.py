#!/usr/bin/env python
#
# sceneopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import copy
import logging

import props

import fsl.data.strings as strings

import canvasopts


log = logging.getLogger(__name__)


class SceneOpts(props.HasProperties):
    """The ``SceneOpts`` class defines settings which are applied to
    :class:`.CanvasPanel` views.
    """

    showCursor      = copy.copy(canvasopts.SliceCanvasOpts.showCursor)
    zoom            = copy.copy(canvasopts.SliceCanvasOpts.zoom)
    bgColour        = copy.copy(canvasopts.SliceCanvasOpts.bgColour)
    cursorColour    = copy.copy(canvasopts.SliceCanvasOpts.cursorColour)
    resolutionLimit = copy.copy(canvasopts.SliceCanvasOpts.resolutionLimit)
    renderMode      = copy.copy(canvasopts.SliceCanvasOpts.renderMode)
    softwareMode    = copy.copy(canvasopts.SliceCanvasOpts.softwareMode)

    
    showColourBar = props.Boolean(default=False)

    
    colourBarLocation  = props.Choice(
        ('top', 'bottom', 'left', 'right'),
        labels=[strings.choices['SceneOpts.colourBarLocation.top'],
                strings.choices['SceneOpts.colourBarLocation.bottom'],
                strings.choices['SceneOpts.colourBarLocation.left'],
                strings.choices['SceneOpts.colourBarLocation.right']])

    
    colourBarLabelSide = props.Choice(
        ('top-left', 'bottom-right'),
        labels=[strings.choices['ColourBarCanvas.labelSide.top-left'],
                strings.choices['ColourBarCanvas.labelSide.bottom-right']])

    
    performance = props.Choice(
        (1, 2, 3, 4, 5),
        default=5,
        labels=[strings.choices['SceneOpts.performance.1'],
                strings.choices['SceneOpts.performance.2'],
                strings.choices['SceneOpts.performance.3'],
                strings.choices['SceneOpts.performance.4'],
                strings.choices['SceneOpts.performance.5']])
    """User controllable performacne setting.

    This property is linked to the :attr:`renderMode`,
    :attr:`resolutionLimit`, and :attr:`softwareMode` properties. Setting the
    performance to a low value will result in faster rendering time, at the
    cost of reduced features, and poorer rendering quality.

    See the :meth:`__onPerformanceChange` method.
    """


    def __init__(self):
        
        name = '{}_{}'.format(type(self).__name__, id(self))
        self.addListener('performance', name, self.__onPerformanceChange)
        
        self.__onPerformanceChange()


    def __onPerformanceChange(self, *a):
        """Called when the :attr:`performance` property changes.

        Changes the values of the :attr:`renderMode`, :attr:`softwareMode`
        and :attr:`resolutionLimit` properties accoridng to the performance
        setting.
        """

        if   self.performance == 5:
            self.renderMode      = 'onscreen'
            self.softwareMode    = False
            self.resolutionLimit = 0
            
        elif self.performance == 4:
            self.renderMode      = 'onscreen'
            self.softwareMode    = True
            self.resolutionLimit = 0

        elif self.performance == 3:
            self.renderMode      = 'offscreen'
            self.softwareMode    = True
            self.resolutionLimit = 0 
            
        elif self.performance == 2:
            self.renderMode      = 'prerender'
            self.softwareMode    = True
            self.resolutionLimit = 0

        elif self.performance == 1:
            self.renderMode      = 'prerender'
            self.softwareMode    = True
            self.resolutionLimit = 1

        log.debug('Performance settings changed: '
                  'renderMode={}, '
                  'softwareMode={}, '
                  'resolutionLimit={}'.format(
                      self.renderMode,
                      self.softwareMode,
                      self.resolutionLimit))
