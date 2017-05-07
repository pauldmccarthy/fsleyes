#!/usr/bin/env python
#
# shopts.py - The SHOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SHOpts` class, a :class:`.VectorOpts`
class for rendering :class:`.Image` instances which contain fibre orientation
distributions (FODs) in the form of spherical harmonic (SH) coefficients.
"""


import os.path       as op

import numpy         as np

import fsleyes_props as props

import                  fsleyes
from . import           vectoropts


SH_COEFFICIENT_TYPE = {
    1   : ('asym', 0),
    9   : ('asym', 2),
    25  : ('asym', 4),
    49  : ('asym', 6),
    81  : ('asym', 8),
    121 : ('asym', 10),
    169 : ('asym', 12),
    225 : ('asym', 14),
    289 : ('asym', 16),
    1   : ('sym',  0),
    6   : ('sym',  2),
    15  : ('sym',  4),
    28  : ('sym',  6),
    45  : ('sym',  8),
    66  : ('sym',  10),
    91  : ('sym',  12),
    120 : ('sym',  14),
    153 : ('sym',  16),
}
"""``Image`` files which contain SH coefficients may be symmetric (only
containing coefficients for even spherical functions) or asymmetric
(containing coefficients for odd and even functions). This dictionary provides
mappings from the number coefficients (the volumes contained in the image), to
the file type (either symmetric [``'sym'``] or asymmetric [``'asym'``), and the
maximum SH order that was used in generating the coefficients.
"""


class SHOpts(vectoropts.VectorOpts):
    """The ``SHOpts`` is used for rendering class for rendering :class:`.Image`
    instances which contain fibre orientation distributions (FODs) in the form
    of spherical harmonic (SH) coefficients. A ``SHOpts`` instance will be
    used for ``Image`` overlays with a :attr:`.Displaty.overlayType` set to
    ``'sh'``.


    A collection of pre-calculated SH basis function parameters are stored in
    the ``assets/sh/`` directory. Depending on the SH order that was used in
    the fibre orientation, and the desired display resolution (controlled by
    :attr:`shResolution`), a different set of parameters needs to be used.
    The :meth:`getSHParameters` method will load and return the corrrect
    set of parameters.
    """


    shResolution = props.Int(minval=3, maxval=10, default=5)
    """Resolution of the sphere used to display the FODs at each voxel. The
    value is equal to the number of iterations that an isocahedron, starting
    with 12 vertices, is tessellated. The resulting number of vertices is
    as follows:


    ==================== ==================
    Number of iterations Number of vertices
    3                    92
    4                    162
    5                    252
    6                    362
    7                    492
    8                    642
    9                    812
    10                   1002
    ==================== ==================
    """


    shOrder = props.Choice(allowStr=True)
    """Maximum spherical harmonic order to visualise. This is populated in
    :meth:`__init__`.
    """


    size = props.Percentage(minval=10, maxval=500, default=100)
    """Display size - this is simply a linear scaling factor. """


    lighting = props.Boolean(default=False)
    """Apply a simple directional lighting model to the FODs. """


    radiusThreshold = props.Real(minval=0.0, maxval=1.0, default=0.05)
    """FODs with a maximum radius that is below this threshold are not shown.
    """


    colourMode = props.Choice(('direction', 'radius'))
    """How to colour each FOD. This property is overridden if the
    :attr:`.VectorOpts.colourImage` is set.

      - ``'direction'`` The vertices of an FOD are coloured according to their
                        x/y/z location (see :attr:`xColour`, :attr:`yColour`,
                        and :attr:`zColour`).

      - ``'radius'``    The vertices of an FOD are coloured according to their
                        distance from the FOD centre (see :attr:`colourMap`).
    """


    def __init__(self, *args, **kwargs):

        vectoropts.VectorOpts.__init__(self, *args, **kwargs)

        ncoefs           = self.overlay.shape[3]
        shType, maxOrder = SH_COEFFICIENT_TYPE.get(ncoefs)

        if shType is None:
            raise ValueError('{} does not look like a SH '
                             'image'.format(self.overlay.name))

        self.__maxOrder = maxOrder
        self.__shType   = shType

        # If this Opts instance has a parent,
        # the shOrder choices will be inherited
        if self.getParent() is None:

            if   shType == 'sym':  vizOrders = range(0, self.__maxOrder + 1, 2)
            elif shType == 'asym': vizOrders = range(0, self.__maxOrder + 1)

            self.getProp('shOrder').setChoices(list(vizOrders), instance=self)
            self.shOrder = vizOrders[-1]


    @property
    def shType(self):
        """Returns either ``'sym'`` or ``'asym'``, depending on the type
        of the SH coefficients contained in the file.
        """
        return self.__shType


    @property
    def maxOrder(self):
        """Returns the maximum SH order that was used to generate the
        coefficients of the SH image.
        """
        return self.__maxOrder


    def getSHParameters(self):
        """Load and return a ``numpy`` array containing pre-calculated SH
        function parameters for the curert maximum SH order and display
        resolution. The returned array has the shape ``(N, C)``, where ``N``
        is the number of vertices used to represent each FOD, and ``C`` is
        the number of SH coefficients.
        """

        # TODO Adjust matrix if shOrder is
        #      less than its maximum possible
        #      value for this image.
        #
        #      Also, calculate the normal vectors.

        resolution = self.shResolution
        ncoefs     = self.overlay.shape[3]
        order      = self.shOrder
        ftype, _   = SH_COEFFICIENT_TYPE[ncoefs]
        fname     = op.join(
            fsleyes.assetDir,
            'assets',
            'sh',
            '{}_coef_{}_{}.txt'.format(ftype, resolution, order))

        params = np.loadtxt(fname)

        if len(params.shape) == 1:
            params = params.reshape((-1, 1))

        return params


    def getVertices(self):
        """Loads and returns a ``numpy`` array of shape ``(N, 3)``, containing
        ``N`` vertices of a tessellated sphere.
        """
        fname = op.join(
            fsleyes.assetDir,
            'assets',
            'sh',
            'vert_{}.txt'.format(self.shResolution))

        return np.loadtxt(fname)


    def getIndices(self):
        """Loads and returns a 1D ``numpy`` array, containing indices into
        the vertex array, specifying the order in which they are to be drawn
        as triangles.
        """
        fname = op.join(
            fsleyes.assetDir,
            'assets',
            'sh',
            'face_{}.txt'.format(self.shResolution))

        return np.loadtxt(fname).flatten()
