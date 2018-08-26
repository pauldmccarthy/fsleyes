#!/usr/bin/env python
#
# mipopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from   fsl.utils.platform import platform as fslplatform

import fsleyes_props                      as props

from . import colourmapopts               as cmapopts
from . import                                volumeopts


class MIPOpts(cmapopts.ColourMapOpts, volumeopts.NiftiOpts):


    window = props.Real(minval=0, maxval=1, clamped=True)


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
