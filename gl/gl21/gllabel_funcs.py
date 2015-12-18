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

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)

    vertAtts     = ['vertex',       'voxCoord',   'texCoord']
    vertUniforms = []
    fragUniforms = ['imageTexture', 'lutTexture', 'voxValXform',
                    'imageShape',   'numLabels',  'outline',
                    'outlineOffsets']

    self.shaders    = shaders.compileShaders(vertShaderSrc, fragShaderSrc)
    self.shaderVars = shaders.getShaderVars(self.shaders,
                                            vertAtts,
                                            vertUniforms,
                                            fragUniforms)


def updateShaderState(self):
    """Updates all shader program variables. """

    opts  = self.displayOpts
    svars = self.shaderVars

    gl.glUseProgram(self.shaders)

    gl.glUniform1f( svars['outline'],       opts.outline)
    gl.glUniform1f( svars['numLabels'],     opts.lut.max() + 1)
    gl.glUniform3fv(svars['imageShape'], 1, np.array(self.image.shape[:3],
                                                     dtype=np.float32))
    
    vvx = self.imageTexture.voxValXform.ravel('C')
    gl.glUniformMatrix4fv(svars['voxValXform'], 1, False, vvx)

    outlineOffsets = opts.outlineWidth / \
                     np.array(self.image.shape[:3], dtype=np.float32)
    
    if opts.transform == 'affine':
        minOffset = outlineOffsets.min()
        outlineOffsets = np.array([minOffset] * 3)
    else:
        outlineOffsets[self.zax] = -1

    gl.glUniform3fv(svars['outlineOffsets'], 1, outlineOffsets)

    gl.glUniform1i(svars['imageTexture'], 0)
    gl.glUniform1i(svars['lutTexture'],   1) 

    gl.glUseProgram(0)


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
