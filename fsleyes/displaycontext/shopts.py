#!/usr/bin/env python
#
# shopts.py - The SHOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SHOpts` class, a :class:`.DisplayOpts`
class for rendering :class:`.Image` instances which contain fibre orientation
distributions (FODs) in the form of spherical harmonic (SH) coefficients.
"""


import os.path as op

import numpy   as np

import            props

import            fsleyes
from . import     volumeopts


SH_COEFFICIENT_TYPE = {
    45 : 'sym',
    81 : 'asym',
}
"""``Image`` files which contain SH coefficients may be symmetric (only
containing coefficients for even spherical functions) or asymmetric dictionary
provides mappings from the number of volumes contained in the image, to the
file type (either symmetric [``'sym'``] or asymmetric [``'asym'``).
"""


class SHOpts(volumeopts.Nifti1Opts):
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

    
    shResolution = props.Choice((16,))
    """Resolution of the sphere used to display the FODs at each voxel. This
    defines the number of latitude and longitude angles sampled around the
    sphere, so the total number of vertices used will be
    ``shResolution ** 2``.
    """

    
    size = props.Percentage(minval=10, maxval=500, default=100)
    """Display size - this is simply a linear scaling factor. """
    

    lighting = props.Boolean(default=True)
    """Apply a simple directional lighting model to the FODs. """

    
    neuroFlip = props.Boolean(default=True)
    """If ``True``, and the displayed image looks like it is in neurological
    orientation, FODs are flipped along the x-axis. 
    """ 

    
    radiusThreshold = props.Real(minval=0.0, maxval=1.0, default=0.0)
    """FODs with a maximum radius that is below this threshold are not shown.
    """

    
    colourMode = props.Choice(('direction', 'radius'))
    """How to colour each FOD.
    
      - ``'direction'`` The vertices of an FOD are coloured according to their
                        x/y/z location (see :attr:`xColour`, :attr:`yColour`,
                        and :attr:`zColour`).

      - ``'radius'``    The vertices of an FOD are coloured according to their
                        distance from the FOD centre (see :attr:`colourMap`).
    """


    colourMap = props.ColourMap()
    """Colour map used to colour FODs, when the :attr:`colourMode` is
    ``'radius'``.
    """


    xColour = props.Colour(default=(1, 0, 0))
    """Colour used to denote X axis direction, when the :attr:`colourMode` is
    ``'direction'``.
    """
    
    yColour = props.Colour(default=(0, 1, 0))
    """Colour used to denote Y axis direction, when the :attr:`colourMode` is
    ``'direction'``.
    """ 

    
    zColour = props.Colour(default=(0, 0, 1))
    """Colour used to denote Z axis direction, when the :attr:`colourMode` is
    ``'direction'``.
    """ 


    def getSHParameters(self):
        """Load and return a ``numpy`` array containing pre-calculated SH
        function parameters for the image order and the display resolution.
        """

        resolution = self.shResolution ** 2
        order      = self.overlay.shape[3]
        fileType   = SH_COEFFICIENT_TYPE[order]
        
        return np.loadtxt(op.join(
            fsleyes.assetDir,
            'assets',
            'sh',
            '{}x{}_{}.txt'.format(resolution, order, fileType)))
