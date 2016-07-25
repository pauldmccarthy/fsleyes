#!/usr/bin/env python
#
# shopts.py - The SHOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SHOpts` class, a :class:`.DisplayOpts`
class for rendering :class:`.Image` instances which contain SH data.
"""

import os.path as op

import numpy   as np

import            props

import            fsleyes
from . import     volumeopts


SH_TYPE = {
    45 : 'sym',
    81 : 'asym',
}


class SHOpts(volumeopts.Nifti1Opts):


    shResolution  = props.Choice((16,))
    
    size          = props.Percentage(minval=10, maxval=500, default=100)

    lighting      = props.Boolean(default=True)

    neuroFlip     = props.Boolean(default=True)

    radiusThreshold = props.Real(minval=0.0, maxval=1.0, default=0.0)

    colourMode    = props.Choice(('direction', 'radius'))


    colourMap     = props.ColourMap()
    # For 'radius'


    xColour       = props.Colour(default=(1, 0, 0))
    yColour       = props.Colour(default=(0, 1, 0))
    zColour       = props.Colour(default=(0, 0, 1))
    # For 'direction'


    def getCoefficients(self):

        resolution = self.shResolution ** 2
        order      = self.overlay.shape[3]
        fileType   = SH_TYPE[order]
        
        return np.loadtxt(op.join(
            fsleyes.assetDir,
            'assets',
            'sh',
            '{}x{}_{}.txt'.format(resolution, order, fileType)))
