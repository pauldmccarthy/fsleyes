#!/usr/bin/env python
#
# tractogramopts.py - The TractogramOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TractogramOpts` class, which defines
display properties for :class:`.Tractogram` overlays.
"""

import fsleyes_props as props

from . import display       as fsldisplay
from . import colourmapopts as cmapopts


class TractogramOpts(cmapopts.ColourMapOpts, fsldisplay.DisplayOpts):
    """
    """

    refImage = props.Choice()

    coordSpace = props.Choice(('affine', 'pixdim', 'pixdim-flip', 'id'))

    colourBy = props.Choice((None, 'orientation', 'pointData', 'streamlineData'))

    pointData = props.Choice((None,))

    streamlineData = props.Choice((None,))
