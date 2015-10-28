#!/usr/bin/env python
#
# gllabel_funcs.py - OpenGL 1.4 functions used by the GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLLabel`
class to render :class:`.Image` overlays in an OpenGL 1.4 compatible manner.


Rendering of a ``GLLabel`` is very similar to that of a :class:`.GLVolume`;
therefore, the ``preDraw``, ``draw``, ``drawAll`` and ``postDraw`` functions
defined in the :mod:`.gl14.glvolume_funcs` are re-used by this module.
"""


import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.fsleyes.gl.shaders as shaders

import glvolume_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions.
    """
    self.vertexProgram   = None
    self.fragmentProgram = None
    
    compileShaders(   self)
    updateShaderState(self) 


def destroy(self):
    """Deletes handles to the vertex/fragment shader programs. """
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 


def compileShaders(self):
    """Compiles the vertex and fragment shader programs used to render
    :class:`.GLLabel` instances.
    """
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


def updateShaderState(self):
    """Updates all shader program variables. """
    
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
