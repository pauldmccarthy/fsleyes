#!/usr/bin/env python
#
# csdopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

from . import volumeopts


class CSDOpts(volumeopts.Nifti1Opts):

    lighting  = props.Boolean(default=True)

    neuroFlip = props.Boolean(default=True)
