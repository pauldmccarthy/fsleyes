#!/usr/bin/env python
#
# glrgbvector.py - Display vector images in RGB mode.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This mdoule provides the :class:`GLRGBVector` class, for displaying 3D
vector images in RGB mode.
"""

import numpy                   as np
import OpenGL.GL               as gl


import fsl.fsleyes.gl          as fslgl
import fsl.fsleyes.gl.glvector as glvector


class GLRGBVector(glvector.GLVector):


    def __prefilter(self, data):
        return np.abs(data)


    def __init__(self, image, display):

        glvector.GLVector.__init__(self, image, display, self.__prefilter)
        fslgl.glrgbvector_funcs.init(self)

        self.displayOpts.addListener('interpolation',
                                     self.name,
                                     self.__interpChanged)


    def destroy(self):
        self.displayOpts.removeListener('interpolation', self.name)
        glvector.GLVector.destroy(self)


    def refreshImageTexture(self):
        glvector.GLVector.refreshImageTexture(self)
        self.__setInterp()

        
    def __setInterp(self):
        opts = self.displayOpts

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR 
        
        self.imageTexture.set(interp=interp)

        
    def __interpChanged(self, *a):
        self.__setInterp()
        self.updateShaderState()
        self.onUpdate()


    def compileShaders(self):
        fslgl.glrgbvector_funcs.compileShaders(self)
        

    def updateShaderState(self):
        fslgl.glrgbvector_funcs.updateShaderState(self)


    def preDraw(self):
        glvector.GLVector.preDraw(self)
        fslgl.glrgbvector_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.glrgbvector_funcs.draw(self, zpos, xform)

    
    def drawAll(self, zposes, xforms):
        fslgl.glrgbvector_funcs.drawAll(self, zposes, xforms) 

    
    def postDraw(self):
        glvector.GLVector.postDraw(self)
        fslgl.glrgbvector_funcs.postDraw(self) 
