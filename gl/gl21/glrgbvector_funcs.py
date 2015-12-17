#!/usr/bin/env python
#
# glrgbvector_funcs.py - OpenGL 2.1 functions used by the GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLRGBVector`
class to render :class:`.Image` overlays as RGB vector images in an OpenGL 2.1
compatible manner.


Rendering of a ``GLRGBVector`` is very similar to that of a
:class:`.GLVolume`; therefore, the ``preDraw``, ``draw``, ``drawAll`` and
``postDraw`` functions defined in the :mod:`.gl21.glvolume_funcs` are re-used
by this module.
"""


import numpy                as np
import OpenGL.GL            as gl
import OpenGL.raw.GL._types as gltypes

import fsl.fsleyes.gl.shaders as shaders
import                           glvolume_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions, and creates a GL vertex buffer for storing vertex
    information.
    """

    self.shaders = None

    compileShaders(   self)
    updateShaderState(self)

    self.vertexAttrBuffer = gl.glGenBuffers(1)


def destroy(self):
    """Destroys the vertex buffer and vertex/fragment shaders created
    in :func:`init`.
    """
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexAttrBuffer))
    gl.glDeleteProgram(self.shaders)

    
def compileShaders(self):
    """Compiles the vertex/fragment shaders used for drawing
    :class:`.GLRGBVector` instances. Stores references to the shader
    programs, and to all shader variables on the ``GLRGBVector`` instance.
    """

    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders) 
    
    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    shaderVars   = {}

    vertUniforms = []
    vertAtts     = ['vertex', 'voxCoord', 'texCoord']

    fragUniforms = ['imageTexture',   'modulateTexture', 'clipTexture',
                    'clipLow',        'clipHigh',        'xColourTexture',
                    'yColourTexture', 'zColourTexture',  'voxValXform',
                    'cmapXform',      'imageShape',      'useSpline']

    for va in vertAtts:
        shaderVars[va] = gl.glGetAttribLocation(self.shaders, va)
        
    for vu in vertUniforms:
        shaderVars[va] = gl.glGetUniformLocation(self.shaders, vu)

    for fu in fragUniforms:
        if fu in shaderVars:
            continue
        shaderVars[fu] = gl.glGetUniformLocation(self.shaders, fu)

    self.shaderVars = shaderVars


def updateShaderState(self):
    """Updates all shader program variables. """

    opts  = self.displayOpts
    svars = self.shaderVars

    # The coordinate transformation matrices for 
    # each of the three colour textures are identical
    voxValXform     = self.imageTexture.voxValXform
    invClipValXform = self.clipTexture .invVoxValXform
    cmapXform       = self.xColourTexture.getCoordinateTransform()
    useSpline       = opts.interpolation == 'spline'
    imageShape      = np.array(self.vectorImage.shape, dtype=np.float32)
    clippingRange   = opts.clippingRange

    # Transform the clip threshold into
    # the texture value range, so the
    # fragment shader can compare texture
    # values directly to it.
    if opts.clipImage is not None:
        clipLow  = clippingRange[0] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
        clipHigh = clippingRange[1] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
    else:
        clipLow  = 0
        clipHigh = 1
    
    gl.glUseProgram(self.shaders)

    gl.glUniform1f( svars['useSpline'],     useSpline)
    gl.glUniform3fv(svars['imageShape'], 1, imageShape)

    gl.glUniformMatrix4fv(svars['voxValXform'], 1, False, voxValXform)
    gl.glUniformMatrix4fv(svars['cmapXform'],   1, False, cmapXform)

    gl.glUniform1f(svars['clipLow'],         clipLow)
    gl.glUniform1f(svars['clipHigh'],        clipHigh)
    gl.glUniform1i(svars['imageTexture'],    0)
    gl.glUniform1i(svars['modulateTexture'], 1)
    gl.glUniform1i(svars['clipTexture'],     2)
    gl.glUniform1i(svars['xColourTexture'],  3)
    gl.glUniform1i(svars['yColourTexture'],  4)
    gl.glUniform1i(svars['zColourTexture'],  5)

    gl.glUseProgram(0)


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
