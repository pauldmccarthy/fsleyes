#!/usr/bin/env python
#
# maskopts.py - The MaskOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MaskOpts` class, which defines settings
for displaying an :class:`.Image` overlay as a binary mask.
"""


import props

import fsleyes.strings as strings
from . import             volumeopts


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
