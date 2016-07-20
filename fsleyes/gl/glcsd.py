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

        res   = self.displayOpts.csdResolution ** 2
        shape = self.image.shape
        radii = np.zeros(voxels.shape[0] * res, dtype=np.uint8)
        coef  = self.coefficients        

        for i, (x, y, z) in enumerate(voxels):

            if any((x <  0,
                    y <  0,
                    z <  0,
                    x >= shape[0],
                    y >= shape[1],
                    z >= shape[2])):
                continue

            si           = i  * res
            ei           = si + res

            data         = self.image[int(x), int(y), int(z), :]
            radii[si:ei] = np.dot(coef, data) * 255

        return radii


    def ready(self):
        return True


    def preDraw(self):
        fslgl.glcsd_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.glcsd_funcs.draw(self, zpos, xform)


    def postDraw(self):
        fslgl.glcsd_funcs.postDraw(self)
