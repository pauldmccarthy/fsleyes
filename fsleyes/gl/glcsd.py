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
import               fsleyes


log = logging.getLogger(__name__)


CSD_TYPE = {
    45 : 'sym',
    81 : 'asym',
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
        opts.addListener('size',       name, self.updateShaderState)
        opts.addListener('lighting',   name, self.updateShaderState)
        opts.addListener('colourMode', name, self.updateShaderState)
        opts.addListener('neuroFlip',  name, self.updateShaderState)

    
    def removeListeners(self):
        
        opts = self.displayOpts
        name = self.name

        opts.removeListener('csdResolution', name)

        
    def updateShaderState(self, *a):
        fslgl.glcsd_funcs.updateShaderState(self)
        self.notify()

        
    def csdResChanged(self, *a):

        opts        = self.displayOpts
        order       = self.image.shape[3]
        resolution  = opts.csdResolution ** 2
        fileType    = CSD_TYPE[order]
        
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


    def draw(self, zpos, xform=None, bbox=None):
        fslgl.glcsd_funcs.draw(self, zpos, xform, bbox)


    def postDraw(self):
        fslgl.glcsd_funcs.postDraw(self)
