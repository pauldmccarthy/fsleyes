#!/usr/bin/env python
#
# glrgbvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                as np
import OpenGL.GL            as gl
import OpenGL.raw.GL._types as gltypes

import fsl.fsleyes.gl.shaders as shaders
import                           glvolume_funcs


def init(self):
    self.shaders = None

    compileShaders(   self)
    updateShaderState(self)

    self.vertexAttrBuffer = gl.glGenBuffers(1)


def destroy(self):
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexAttrBuffer))
    gl.glDeleteProgram(self.shaders)

    
def compileShaders(self):

    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders) 
    
    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.vertexPos          = gl.glGetAttribLocation( self.shaders,
                                                      'vertex')
    self.voxCoordPos        = gl.glGetAttribLocation( self.shaders,
                                                      'voxCoord')
    self.texCoordPos        = gl.glGetAttribLocation( self.shaders,
                                                      'texCoord') 
    self.imageTexturePos    = gl.glGetUniformLocation(self.shaders,
                                                      'imageTexture')
    self.modTexturePos      = gl.glGetUniformLocation(self.shaders,
                                                      'modTexture')
    self.xColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'xColourTexture')
    self.yColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'yColourTexture') 
    self.zColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'zColourTexture')
    self.modThresholdPos    = gl.glGetUniformLocation(self.shaders,
                                                      'modThreshold') 
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                      'useSpline')
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                      'imageShape')
    self.voxValXformPos     = gl.glGetUniformLocation(self.shaders,
                                                      'voxValXform')
    self.cmapXformPos       = gl.glGetUniformLocation(self.shaders,
                                                      'cmapXform') 


def updateShaderState(self):

    opts = self.displayOpts

    # The coordinate transformation matrices for 
    # each of the three colour textures are identical
    voxValXform = self.imageTexture.voxValXform
    cmapXform   = self.xColourTexture.getCoordinateTransform()
    useSpline   = opts.interpolation == 'spline'
    imageShape  = np.array(self.image.shape, dtype=np.float32)

    gl.glUseProgram(self.shaders)

    gl.glUniform1f( self.useSplinePos,     useSpline)
    gl.glUniform3fv(self.imageShapePos, 1, imageShape)

    gl.glUniformMatrix4fv(self.voxValXformPos, 1, False, voxValXform)
    gl.glUniformMatrix4fv(self.cmapXformPos,   1, False, cmapXform)

    gl.glUniform1f(self.modThresholdPos,   opts.modThreshold / 100.0)
    gl.glUniform1i(self.imageTexturePos,   0)
    gl.glUniform1i(self.modTexturePos,     1)
    gl.glUniform1i(self.xColourTexturePos, 2)
    gl.glUniform1i(self.yColourTexturePos, 3)
    gl.glUniform1i(self.zColourTexturePos, 4)

    gl.glUseProgram(0)


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
