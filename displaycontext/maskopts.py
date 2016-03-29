#!/usr/bin/env python
#
# maskopts.py - The MaskOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MaskOpts` class, which defines settings
for displaying an :class:`.Image` overlay as a binary mask.
"""


import numpy as np

import props

import fsl.fsleyes.strings as strings
import                        volumeopts


class MaskOpts(volumeopts.Nifti1Opts):
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
        are passed through to the :class:`.Nifti1Opts` constructor.
        """

        if np.prod(overlay.shape) > 2 ** 30:
            sample = overlay.data[..., overlay.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(overlay.data.min())
            self.dataMax = float(overlay.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 100.0

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
        self.clippingRange   = (self.dataMin - 1, self.dataMax + 1)
        self.interpolation   = 'none'
        self.invertClipping  = False
        self.useNegativeCmap = False
        self.clipImage       = None

        self.threshold.xmin = self.dataMin - dMinDistance
        self.threshold.xmax = self.dataMax + dMinDistance
        self.threshold.xlo  = self.dataMin + dMinDistance
        self.threshold.xhi  = self.dataMax + dMinDistance 

        volumeopts.Nifti1Opts.__init__(self, overlay, *args, **kwargs)
