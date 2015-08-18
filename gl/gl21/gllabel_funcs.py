#!/usr/bin/env python
#
# gllabel_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fsleyes.gl.shaders as shaders
import                           glvolume_funcs

def compileShaders(self):

    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)

    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.vertexPos         = gl.glGetAttribLocation( self.shaders,
                                                     'vertex')
    self.voxCoordPos       = gl.glGetAttribLocation( self.shaders,
                                                     'voxCoord')
    self.texCoordPos       = gl.glGetAttribLocation( self.shaders,
                                                     'texCoord') 
    self.imageTexturePos   = gl.glGetUniformLocation(self.shaders,
                                                     'imageTexture')
    self.lutTexturePos     = gl.glGetUniformLocation(self.shaders,
                                                     'lutTexture')
    self.voxValXformPos    = gl.glGetUniformLocation(self.shaders,
                                                     'voxValXform') 
    self.imageShapePos     = gl.glGetUniformLocation(self.shaders,
                                                     'imageShape')
    self.useSplinePos      = gl.glGetUniformLocation(self.shaders,
                                                     'useSpline')
    self.numLabelsPos      = gl.glGetUniformLocation(self.shaders,
                                                     'numLabels')
    self.outlinePos        = gl.glGetUniformLocation(self.shaders,
                                                     'outline') 
    self.outlineOffsetsPos = gl.glGetUniformLocation(self.shaders,
                                                     'outlineOffsets')


def init(self):
    self.shaders = None

    compileShaders(   self)
    updateShaderState(self)

    self.vertexAttrBuffer = gl.glGenBuffers(1)
    

def destroy(self):
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexAttrBuffer))
    gl.glDeleteProgram(self.shaders) 


def updateShaderState(self):

    opts = self.displayOpts

    gl.glUseProgram(self.shaders)

    gl.glUniform1f( self.outlinePos,       opts.outline)
    gl.glUniform1f( self.numLabelsPos,     opts.lut.max() + 1)
    gl.glUniform3fv(self.imageShapePos, 1, np.array(self.image.shape[:3],
                                                     dtype=np.float32))
    
    vvx = self.imageTexture.voxValXform.ravel('C')
    gl.glUniformMatrix4fv(self.voxValXformPos, 1, False, vvx)

    outlineOffsets = opts.outlineWidth / \
                     np.array(self.image.shape[:3], dtype=np.float32)
    
    if opts.transform == 'affine':
        minOffset = outlineOffsets.min()
        outlineOffsets = np.array([minOffset] * 3)
    else:
        outlineOffsets[self.zax] = -1

    gl.glUniform3fv(self.outlineOffsetsPos, 1, outlineOffsets)

    gl.glUniform1i(self.imageTexturePos, 0)
    gl.glUniform1i(self.lutTexturePos,   1) 

    gl.glUseProgram(0)


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
