#!/usr/bin/env python
#
# csdopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

from . import volumeopts


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
