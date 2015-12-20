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


import numpy                       as np

import fsl.fsleyes.gl.shaders      as shaders
import fsl.fsleyes.gl.glsl.program as glslprogram
import                                glvolume_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions, and creates a GL buffer for storing vertex attributes.
    """    
    self.shader = None

    compileShaders(   self)
    updateShaderState(self)
    

def destroy(self):
    """Destroys the shader programs, and the vertex buffer. """
    self.shader.delete()
    self.shader = None


def compileShaders(self):
    """Compiles vertex/fragment shader programs used to render
    :class:`.GLLabel` instances, and stores the positions of all
    shader variables as attributes on the :class:`.GLLabel` instance.
    """

    if self.shader is not None:
        self.shader.delete()

    vertSrc = shaders.getVertexShader(  self)
    fragSrc = shaders.getFragmentShader(self)

    self.shader = glslprogram.ShaderProgram(vertSrc, fragSrc)


def updateShaderState(self):
    """Updates all shader program variables. """

    opts   = self.displayOpts
    shader = self.shader

    imageShape      = np.array(self.image.shape[:3])
    vvx             = self.imageTexture.voxValXform
    outlineOffsets  = opts.outlineWidth / imageShape
    
    if opts.transform == 'affine':
        minOffset = outlineOffsets.min()
        outlineOffsets = np.array([minOffset] * 3)
    else:
        outlineOffsets[self.zax] = -1 

    shader.load()

    shader.set('outline',        opts.outline)
    shader.set('numLabels',      opts.lut.max() + 1)
    shader.set('imageShape',     imageShape)
    shader.set('voxValXform',    vvx)
    shader.set('outlineOffsets', outlineOffsets)
    shader.set('imageTexture',   0)
    shader.set('lutTexture',     1)

    shader.unload()


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
