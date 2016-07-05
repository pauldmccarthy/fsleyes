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


class GLCSD(globject.GLImageObject):
    """
    """

    def __init__(self, image, display, xax, yax):
        """
        """
        
        globject.GLImageObject.__init__(self, image, display, xax, yax)

        self.full       = True
        self.order      = image.shape[3]
        self.resolution = 16
        self.shCoefs    = np.loadtxt(op.join(
            fsleyes.assetDir,
            'assets',
            'csd',
            '{}x{}_{}.txt'.format(self.resolution ** 2,
                                  self.order,
                                  'full' if self.full else 'half')))

        fslgl.glcsd_funcs.init(self)

        
    def destroy(self):
        fslgl.glcsd_funcs.destroy(self)


    def ready(self):
        return True


    def preDraw(self):
        fslgl.glcsd_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.glcsd_funcs.draw(self, zpos, xform)


    def postDraw(self):
        fslgl.glcsd_funcs.postDraw(self)
