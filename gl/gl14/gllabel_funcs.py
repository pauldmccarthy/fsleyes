#!/usr/bin/env python
#
# gllabel_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.fsleyes.gl.shaders as shaders

import glvolume_funcs

def compileShaders(self):
    if self.vertexProgram is not None:
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        
    if self.fragmentProgram is not None:
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 

    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram 


def init(self):
    self.vertexProgram   = None
    self.fragmentProgram = None
    
    compileShaders(   self)
    updateShaderState(self) 


def destroy(self):
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 


def updateShaderState(self):
    opts = self.displayOpts

    # enable the vertex and fragment programs
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    voxValXform  = self.imageTexture.voxValXform
    shape        = list(self.image.shape[:3])
    offsets      = opts.outlineWidth / \
                   np.array(self.image.shape[:3], dtype=np.float32)    
    invNumLabels = 1.0 / (opts.lut.max() + 1)

    if opts.transform == 'affine':
        minOffset = offsets.min()
        offsets   = np.array([minOffset] * 3)
    else:
        offsets[self.zax] = -1

    if opts.outline: offsets = [1] + list(offsets)
    else:            offsets = [0] + list(offsets)

    shaders.setVertexProgramVector(  0, shape + [0])
    shaders.setFragmentProgramMatrix(0, voxValXform)
    shaders.setFragmentProgramVector(4, shape + [0])
    shaders.setFragmentProgramVector(5, [invNumLabels, 0, 0, 0])
    shaders.setFragmentProgramVector(6, offsets)

    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB) 


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
