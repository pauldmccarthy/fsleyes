#!/usr/bin/env python
#
# glmodel_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                  as np
import OpenGL.GL              as gl

import fsl.fsleyes.gl.shaders as shaders


def compileShaders(self):
    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    self.shaders  = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.texPos    = gl.glGetUniformLocation(self.shaders, 'tex')
    self.offsetPos = gl.glGetUniformLocation(self.shaders, 'offsets')


def destroy(self):
    gl.glDeleteProgram(self.shaders)


def updateShaders(self):

    width, height = self._renderTexture.getSize()
    outlineWidth  = self.opts.outlineWidth

    # outlineWidth is a value between 0.0 and 1.0 - 
    # we use this value so that it effectly sets the
    # outline to between 0% and 10% of the model
    # width/height (whichever is smaller)
    outlineWidth *= 10
    offsets = 2 * [min(outlineWidth / width, outlineWidth / height)]
    offsets = np.array(offsets, dtype=np.float32)

    gl.glUseProgram(self.shaders)
    gl.glUniform1i( self.texPos,    0)
    gl.glUniform2fv(self.offsetPos, 1, offsets)
    gl.glUseProgram(0)


def loadShaders(self):
    gl.glUseProgram(self.shaders)


def unloadShaders(self):
    gl.glUseProgram(0)
