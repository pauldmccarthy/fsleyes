#!/usr/bin/env python
#
# csdopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

from . import volumeopts


class CSDOpts(volumeopts.Nifti1Opts):

    lighting      = props.Boolean(default=True)

    neuroFlip     = props.Boolean(default=True)

    csdResolution = props.Choice((16,))

    size          = props.Percentage(minval=10, maxval=500, default=100)

    inMemory      = props.Boolean()

    colourMode    = props.Choice(('radius', 'direction', 'constant'))
