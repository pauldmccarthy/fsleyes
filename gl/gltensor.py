#!/usr/bin/env python
#
# gltensor.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import logging

import numpy as np

import glvector

import fsl.fsleyes.gl as fslgl

log = logging.getLogger(__name__)


class GLTensor(glvector.GLVector):

    
    def __init__(self, image, display):
        glvector.GLVector.__init__(self,
                                   image,
                                   display,
                                   prefilter=np.abs,
                                   vectorImage=image.V1())
        fslgl.gltensor_funcs.init(self)


    def destroy(self):
        glvector.GLVector.destroy(self)
        fslgl.gltensor_funcs.destroy(self)

        
    def getDataResolution(self, xax, yax):
        """Overrides :meth:`.GLVector.getDataResolution`. Returns a pixel
        resolution suitable for rendering this ``GLTensor``.
        """

        res       = list(glvector.GLVector.getDataResolution(self, xax, yax))
        res[xax] *= 20
        res[yax] *= 20
        
        return res


    def compileShaders(self):
        fslgl.gltensor_funcs.compileShaders(self)


    def updateShaderState(self):
        fslgl.gltensor_funcs.updateShaderState(self)

        
    def preDraw(self):
        glvector.GLVector.preDraw(self)
        fslgl.gltensor_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.gltensor_funcs.draw(self, zpos, xform)


    def postDraw(self):
        glvector.GLVector.postDraw(self)
        fslgl.gltensor_funcs.postDraw(self)
