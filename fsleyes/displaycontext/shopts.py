#!/usr/bin/env python
#
# csdopts.py - The CSDOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CSDOpts` class, a :class:`.DisplayOpts`
class for rendering :class:`.Image` instances which contain CSD data.
"""

import os.path as op

import numpy   as np

import            props

import            fsleyes
from . import     volumeopts


CSD_TYPE = {
    45 : 'sym',
    81 : 'asym',
}


class CSDOpts(volumeopts.Nifti1Opts):


    csdResolution = props.Choice((16,))
    
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

        resolution = self.csdResolution ** 2
        order      = self.overlay.shape[3]
        fileType   = CSD_TYPE[order]
        
        return np.loadtxt(op.join(
            fsleyes.assetDir,
            'assets',
            'csd',
            '{}x{}_{}.txt'.format(resolution, order, fileType)))
