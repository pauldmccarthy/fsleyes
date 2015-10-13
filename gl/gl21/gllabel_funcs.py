#!/usr/bin/env python
#
# gllabel_funcs.py - OpenGL 2.1 functions used by the GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLLabel`
class to render :class:`.Image` overlays in an OpenGL 2.1 compatible manner.

Rendering of a ``GLLabel`` is very similar to that of a ``GLVolume`` - the
``preDraw``, ``draw``, ``drawAll`` and ``postDraw`` functions defined in the
:mod:`.gl21.glvolume_funcs` are re-used by this module.
"""


import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fsleyes.gl.shaders as shaders
import                           glvolume_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions, and creates a GL buffer for storing vertex attributes.
    """    
    self.shaders = None

    compileShaders(   self)
    updateShaderState(self)

    self.vertexAttrBuffer = gl.glGenBuffers(1)
    

def destroy(self):
    """Destroys the shader programs, and the vertex buffer. """
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexAttrBuffer))
    gl.glDeleteProgram(self.shaders) 


def compileShaders(self):
    """Compiles vertex/fragment shader programs used to render
    :class:`.GLLabel` instances, and stores the positions of all
    shader variables as attributes on the :class:`.GLLabel` instance.
    """

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


def updateShaderState(self):
    """Updates all shader program variables. """

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
