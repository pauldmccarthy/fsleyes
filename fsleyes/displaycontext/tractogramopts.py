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
from . import                  vectoropts


class TractogramOpts(fsldisplay.DisplayOpts,
                     cmapopts.ColourMapOpts,
                     vectoropts.VectorOpts):
    """
    """

    refImage = props.Choice()

    coordSpace = props.Choice(('affine', 'pixdim', 'pixdim-flip', 'id'))

    colourBy = props.Choice((None, 'orientation', 'pointData', 'streamlineData'))

    pointData = props.Choice((None,))

    streamlineData = props.Choice((None,))


    def __init__(self, *args, **kwargs):
        fsldisplay.DisplayOpts  .__init__(self, *args, **kwargs)
        cmapopts  .ColourMapOpts.__init__(self)
        vectoropts.VectorOpts   .__init__(self)

        self.__updateBounds()


    def getDataRange(self):
        return 0, 1


    def __updateBounds(self):

        lo, hi        = self.overlay.bounds
        xlo, ylo, zlo = lo
        xhi, yhi, zhi = hi

        self.bounds = [xlo, xhi, ylo, yhi, zlo, zhi]
