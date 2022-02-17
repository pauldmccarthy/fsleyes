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

    colourMode = props.Choice(('orientation', 'vertexData', 'streamlineData'))
    """Whether to colour streamlines by their orientation (e.g. RGB colouring),
    or whether to colour them by per-vertex or per-streamline data.
    """


    vertexData = props.Choice((None,))
    """Per-vertex data set with which to colour the streamlines, when
    ``colourMode == 'vertexData'``.
    """


    streamlineData = props.Choice((None,))
    """Per-streamline data set with which to colour the streamlines, when
    ``colourMode == 'streamlineData'``.
    """


    lineWidth = props.Int(minval=1, maxval=10, default=1)
    """Width to draw the streamlines. """


    resolution = props.Int(minval=1, maxval=10, default=5, clamped=True)
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

        lo, hi        = self.overlay.bounds
        xlo, ylo, zlo = lo
        xhi, yhi, zhi = hi
        self.bounds   = [xlo, xhi, ylo, yhi, zlo, zhi]

        self.addListener('colourMode',     self.name, self.__dataChanged)
        self.addListener('vertexData',     self.name, self.__dataChanged)
        self.addListener('streamlineData', self.name, self.__dataChanged)


    def __dataChanged(self, *_):
        self.updateDataRange()


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`. Returns the
        current data range to use for colouring - this depends on the
        current :attr:`colourMode`, and selected :attr:`vertexData` or
        :attr:`streamlineData`.
        """
        if self.colourMode == 'vertexData' and \
           self.vertexData is not None:
            vdata = self.overlay.getVertexData(self.vertexData)
            dmin  = np.nanmin(vdata)
            dmax  = np.nanmax(vdata)
        elif self.colourMode == 'streamlineData'and \
             self.streamlineData is not None:
            sdata = self.overlay.getStreamlineData(self.streamlineData)
            dmin  = np.nanmin(sdata)
            dmax  = np.nanmax(sdata)
        else:
            dmin = 0
            dmax = 1

        return dmin, dmax


    @property
    def effectiveColourMode(self):
        """Returns ``'data'`` or ``'orient'``, indicataing whether the
        tractogram should be coloured by streamline orientation, or
        streamline/vertex data.
        """
        cmode = self.colourMode
        sdata = self.streamlineData
        vdata = self.vertexData

        if   cmode == 'vertexData'     and vdata is not None: return 'data'
        elif cmode == 'streamlineData' and sdata is not None: return 'data'
        else:                                                 return 'orient'


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


    def addVertexDataOptions(self, paths):
        """Adds the given sequence of paths as options to the
        :attr:`vertexData` property. It is assumed that the paths refer
        to valid vertex data files for the overlay associated with this
        ``TractogramOpts`` instance.
        """
        self.__addDataSetOptions(self.getProp('vertexData'), paths)


    def addStreamlineDataOptions(self, paths):
        """Adds the given sequence of paths as options to the
        :attr:`streamlineData` property. It is assumed that the paths refer
        to valid streamline data files for the overlay associated with this
        ``TractogramOpts`` instance.
        """
        self.__addDataSetOptions(self.getProp('streamlineData'), paths)


    def __addDataSetOptions(self, prop, paths):
        """Used by :meth:`addVertexDataOptions` and
        :meth:`addStreamlineDataOptions`.
        """
        newPaths = paths
        paths    = prop.getChoices(instance=self)
        paths    = paths + [p for p in newPaths if p not in paths]
        prop.setChoices(paths, instance=self)
