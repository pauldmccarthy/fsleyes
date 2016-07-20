#!/usr/bin/env python
#
# glcsd.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path    as op
import               logging

import numpy      as np


import fsleyes.gl as fslgl
from . import        globject
from . import        textures
import               fsleyes


log = logging.getLogger(__name__)


CSD_FILE_TYPE = {
    45 : 'half',
    81 : 'full',
}


class GLCSD(globject.GLImageObject):
    """
    """

    def __init__(self, image, display, xax, yax):
        """
        """
        
        globject.GLImageObject.__init__(self, image, display, xax, yax)

        self.addListeners()
        self.csdResChanged()

        fslgl.glcsd_funcs.init(self)

        
    def destroy(self):
        self.removeListeners()
        fslgl.glcsd_funcs.destroy(self)


    def addListeners(self):

        opts = self.displayOpts
        name = self.name

        opts.addListener('csdResolution', name, self.csdResChanged,
                         immediate=True)


    
    def removeListeners(self):
        
        opts = self.displayOpts
        name = self.name

        opts.removeListener('csdResolution', name)


    def csdResChanged(self, *a):

        opts        = self.displayOpts
        order       = self.image.shape[3]
        resolution  = opts.csdResolution ** 2
        fileType    = CSD_FILE_TYPE[order]
        
        self.coefficients = np.loadtxt(op.join(
            fsleyes.assetDir,
            'assets',
            'csd',
            '{}x{}_{}.txt'.format(resolution, order, fileType)))


    def getRadii(self, voxels):

        coef  = self.coefficients

        # TODO Handle out of bounds x/y/z indices
        shape   = self.image.shape[:3]
        x, y, z = voxels.T

        out = (x <  0)        | \
              (y <  0)        | \
              (z <  0)        | \
              (x >= shape[0]) | \
              (y >= shape[1]) | \
              (z >= shape[2])

        x = x[~out]
        y = y[~out]
        z = z[~out]

        # We need to [insert description here when you know more
        #             about the topic].
        # This can be done with a straight matrix multiplication.
        data    = self.image.nibImage.get_data()[x, y, z, :]
        radii   = np.dot(coef, data.T)

        return radii.flatten(order='F')


    def ready(self):
        return True


    def preDraw(self):
        fslgl.glcsd_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.glcsd_funcs.draw(self, zpos, xform)


    def postDraw(self):
        fslgl.glcsd_funcs.postDraw(self)
