#!/usr/bin/env python
#
# maskopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import props

import fsl.data.strings as strings
import                     volumeopts


class MaskOpts(volumeopts.ImageOpts):

    colour     = props.Colour()
    invert     = props.Boolean(default=False)
    threshold  = props.Bounds(
        ndims=1,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']])

    def __init__(self, overlay, *args, **kwargs):

        if np.prod(overlay.shape) > 2 ** 30:
            sample = overlay.data[..., overlay.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(overlay.data.min())
            self.dataMax = float(overlay.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        #################
        # This is a hack.
        #################

        # Mask images are rendered using GLMask, which
        # inherits from GLVolume. The latter assumes
        # that 'clippingRange', 'interpolation', and
        # 'invertClipping' attributes are present on
        # Opts instances (see the VolumeOpts class).
        # So we're adding dummy attributes to make the
        # GLVolume rendering code happy.
        #
        # TODO Write independent GLMask rendering routines
        # instead of using the GLVolume implementations
        self.clippingRange  = (self.dataMin - 1, self.dataMax + 1)
        self.interpolation  = 'none'
        self.invertClipping = False

        self.threshold.xmin = self.dataMin - dMinDistance
        self.threshold.xmax = self.dataMax + dMinDistance
        self.threshold.xlo  = self.dataMin + dMinDistance
        self.threshold.xhi  = self.dataMax + dMinDistance 
        self.setConstraint('threshold', 'minDistance', dMinDistance)

        volumeopts.ImageOpts.__init__(self, overlay, *args, **kwargs)
