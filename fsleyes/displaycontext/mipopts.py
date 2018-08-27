#!/usr/bin/env python
#
# mipopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.transform                as transform
import fsleyes_props                      as props

from . import colourmapopts               as cmapopts
from . import                                volumeopts


class MIPOpts(cmapopts.ColourMapOpts, volumeopts.NiftiOpts):


    window = props.Percentage(minval=1, clamped=True, default=50)


    minimum = props.Boolean(default=False)


    absolute = props.Boolean(default=False)


    interpolation = props.Choice(('none', 'linear', 'spline'))
    """How the value shown at a real world location is derived from the
    corresponding data value(s). ``none`` is equivalent to nearest neighbour
    interpolation.
    """


    def __init__(self,
                 overlay,
                 display,
                 overlayList,
                 displayCtx,
                 **kwargs):

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslplatform.glVersion) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        volumeopts.NiftiOpts.__init__(self,
                                      overlay,
                                      display,
                                      overlayList,
                                      displayCtx,
                                      **kwargs)
        cmapopts .ColourMapOpts.__init__(self)


        # calculate the approximate number
        # of voxels along the longest diagonal
        # of the image - we use this as the
        # maximum number of samples to take
        x, y, z  = overlay.shape
        xy       = (x * y, (x, y))
        xz       = (x * z, (x, z))
        yz       = (y * z, (y, z))
        ax0, ax1 = max((xy, xz, yz))[1]
        self.numSteps = np.ceil(np.sqrt(ax0 ** 2 + ax1 ** 2))


    def destroy(self):
        """
        """
        cmapopts  .ColourMapOpts.destroy(self)
        volumeopts.NiftiOpts    .destroy(self)


    def getDataRange(self):
        """
        """
        return self.overlay.dataRange


    def calculateRayCastSettings(self, viewmat):
        """
        """

        d2tmat  = self.getTransform('display', 'texture')
        xform   = transform.concat(d2tmat, viewmat)
        cdir    = np.array([0, 0, 1])
        cdir    = transform.transform(cdir, xform, vector=True)
        cdir    = transform.normalise(cdir)

        # sqrt(3) so the maximum number
        # of samplews is taken along the
        # diagonal of a cube
        rayStep = np.sqrt(3) * cdir / self.numSteps

        return cdir, rayStep
