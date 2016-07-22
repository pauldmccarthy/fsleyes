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

    colourMode    = props.Choice(('radius', 'direction'))


    colourMap     = props.ColourMap()
    # For 'radius'


    xColour       = props.Colour()
    yColour       = props.Colour()
    zColour       = props.Colour()
    # For 'direction'
