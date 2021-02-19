#!/usr/bin/env python
#
# mipopts.py - The MIPOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MIPOpts` class, a :class:`.DisplayOpts`
class containing options for rendering maximum intensity projections of
:class:`.Image` overlays. The :class:`MIPOpts` class corresponds to the
``'mip'`` overlay type.

MIP overlays are rendered via the :class:`.GLMIP` class.
"""


import numpy as np

import fsl.transform.affine as affine
import fsleyes_props        as props
import fsleyes.gl           as fslgl

from . import colourmapopts as cmapopts
from . import                  niftiopts


class MIPOpts(cmapopts.ColourMapOpts, niftiopts.NiftiOpts):
    """The ``MIPOpts`` class is used for rendering maximum intensity
    projections of .Image overlays.
    """


    window = props.Percentage(minval=1, clamped=True, default=50)
    """Window over which the MIP is calculated, as a proportion of the image
    length. The window is centered at the current display location.
    """


    minimum = props.Boolean(default=False)
    """Display a minimum intensity projection, rather than maximum. """


    absolute = props.Boolean(default=False)
    """Display an absolute maximum intensity projection. This setting
    overrides the :attr:`minimum` setting.
    """


    interpolation = props.Choice(('none', 'linear', 'spline'))
    """How the value shown at a real world location is derived from the
    corresponding data value(s). ``none`` is equivalent to nearest neighbour
    interpolation.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``MIPOpts`` object.

        All arguments are passed through to the :class:`.NiftiOpts` init
        function.
        """

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        niftiopts.NiftiOpts    .__init__(self, *args, **kwargs)
        cmapopts .ColourMapOpts.__init__(self)

        # calculate the approximate number
        # of voxels along the longest diagonal
        # of the image - we use this to calculate
        # the maximum number of samples to take
        x, y, z  = self.overlay.shape[:3]
        xy       = (x * y, (x, y))
        xz       = (x * z, (x, z))
        yz       = (y * z, (y, z))
        ax0, ax1 = max((xy, xz, yz))[1]
        self.numSteps = np.ceil(np.sqrt(ax0 ** 2 + ax1 ** 2)) * 2


    def destroy(self):
        """Must be called when this ``MIPOpts`` object is no longer needed. """
        cmapopts .ColourMapOpts.destroy(self)
        niftiopts.NiftiOpts    .destroy(self)


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`. Returns the
        :attr:`.Image.dataRange` of the image.
        """
        return self.overlay.dataRange


    def calculateRayCastSettings(self, viewmat):
        """Calculates a camera direction and ray casting step vector, based
        on the given view matrix.
        """

        d2tmat  = self.getTransform('display', 'texture')
        xform   = affine.concat(d2tmat, viewmat)
        cdir    = np.array([0, 0, 1])
        cdir    = affine.transform(cdir, xform, vector=True)
        cdir    = affine.normalise(cdir)

        # sqrt(3) so the maximum number
        # of samplews is taken along the
        # diagonal of a cube
        rayStep = np.sqrt(3) * cdir / self.numSteps

        return cdir, rayStep
