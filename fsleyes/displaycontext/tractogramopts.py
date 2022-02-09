#!/usr/bin/env python
#
# tractogramopts.py - The TractogramOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TractogramOpts` class, which defines
display properties for :class:`.Tractogram` overlays.
"""

import functools            as ft

import numpy                as np

import fsl.transform.affine as affine
import fsleyes_props        as props

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

    lineWidth = props.Int(min=1, max=10, default=1)

    resolution = props.Int(min=1, max=10, default=5, clamped=True)
    """Only relevant when using OpenGL >= 3.3. Streamlines are drawn as tubes -
    this setting defines the resolution at which the tubes are drawn. IF
    resolution <= 2, the streamlines are drawn as lines.
    """


    def __init__(self, *args, **kwargs):
        """
        """
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


    @property
    @ft.lru_cache()
    def orientation(self):
        """Calculates and returns an orientation vector for every vertex of
        every streamline in the tractogram.

        The orientation assigned to a vertex is just the difference between
        that vertex and the previous vertex in the streamline. The first
        vertex in a streamline is given the same orientation as the second
        (i.e. o0 = o1 = (v1 - v0)).
        """

        ovl     = self.overlay
        verts   = ovl.vertices
        orients = np.zeros(verts.shape, dtype=np.float32)

        diffs                   = verts[1:, :] - verts[:-1, :]
        orients[1:, :]          = affine.normalise(diffs)
        orients[ovl.offsets, :] = orients[ovl.offsets + 1, :]

        return orients
