#!/usr/bin/env python
#
# maskopts.py - The MaskOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MaskOpts` class, which defines settings
for displaying an :class:`.Image` overlay as a binary mask.
"""


import logging

import props

import fsleyes.strings as strings
from . import             volumeopts


log = logging.getLogger(__name__)


class MaskOpts(volumeopts.NiftiOpts):
    """The ``MaskOpts`` class defines settings for displaying an
    :class:`.Image` overlay as a binary mask.
    """

    threshold = props.Bounds(
        ndims=1,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']]) 
    """The mask threshold range - values outside of this range are not
    displayed.
    """
    
    invert = props.Boolean(default=False)
    """If ``True``, the :attr:`threshold` range is inverted - values
    inside the range are not shown, and values outside of the range are shown.
    """

    
    colour = props.Colour()
    """The mask colour."""


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``MaskOpts`` instance for the given overlay. All arguments
        are passed through to the :class:`.NiftiOpts` constructor.
        """

        #################
        # This is a hack.
        #################

        # Mask images are rendered using GLMask, which
        # inherits from GLVolume. The latter assumes
        # that the DisplayOpts instance passed to it
        # has the following attributes (see the
        # VolumeOpts class). So we're adding dummy
        # attributes to make the GLVolume rendering
        # code happy.
        #
        # TODO Write independent GLMask rendering routines
        # instead of using the GLVolume implementations 

        dataMin, dataMax = overlay.dataRange
        dRangeLen        = abs(dataMax - dataMin)
        dMinDistance     = dRangeLen / 100.0
 
        self.clippingRange   = (dataMin - 1, dataMax + 1)
        self.interpolation   = 'none'
        self.invertClipping  = False
        self.useNegativeCmap = False
        self.clipImage       = None

        self.threshold.xmin = dataMin - dMinDistance
        self.threshold.xmax = dataMax + dMinDistance
        self.threshold.xlo  = dataMin + dMinDistance
        self.threshold.xhi  = dataMax + dMinDistance 

        volumeopts.NiftiOpts.__init__(self, overlay, *args, **kwargs)

        # The master MaskOpts instance makes 
        # sure that colour[3] and Display.alpha 
        # are consistent w.r.t. each other.
        self.__registered = self.getParent() is None
        if self.__registered:
            self.display.addListener('alpha',
                                     self.name,
                                     self.__alphaChanged,
                                     immediate=True)
            self        .addListener('colour',
                                     self.name,
                                     self.__colourChanged,
                                     immediate=True)


    def destroy(self):
        """Removes some property listeners and calls
        :meth:`.NitfiOpts.destroy`.
        """

        if self.__registered:
            self.display.removeListener('alpha',  self.name)
            self        .removeListener('colour', self.name)

        volumeopts.NiftiOpts.destroy(self)


    def __colourChanged(self, *a):
        """Called when :attr:`.colour` changes. Updates :attr:`.Display.alpha`
        from the alpha component.
        """ 

        alpha = self.colour[3] * 100

        log.debug('Propagating MaskOpts.colour[3] to '
                  'Display.alpha [{}]'.format(alpha))

        with props.skip(self.display, 'alpha', self.name):
            self.display.alpha = alpha


    def __alphaChanged(self, *a):
        """Called when :attr:`.Display.alpha` changes. Updates the alpha
        component of :attr:`.colour`.
        """

        alpha       = self.display.alpha / 100.0
        r, g, b, _  = self.colour

        log.debug('Propagating Display.alpha to MaskOpts.'
                  'colour[3] [{}]'.format(alpha))

        with props.skip(self, 'colour', self.name):
            self.colour = r, g, b, alpha
