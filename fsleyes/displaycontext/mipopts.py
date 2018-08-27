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


    window = props.Percentage(clamped=True, default=50)


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

        # the projection matrix encodes
        # scaling and potential horizontal/vertical
        # inversion

        # the mv matrix encodes 90 degree rotations
        d2tmat = self.getTransform('display', 'texture')
        xform  = transform.concat(d2tmat, viewmat)
        cdir   = np.array([0, 0, 1])
        cdir   = transform.transform(cdir, xform, vector=True)
        cdir   = transform.normalise(cdir)

        # t2dmat = self.getTransform('texture', 'display')
        # xform  = transform.concat(viewmat, t2dmat)

        # rayStep = np.sqrt(3) * cdir / self.numSteps
        rayStep = 0.02 * cdir

        return cdir, rayStep
