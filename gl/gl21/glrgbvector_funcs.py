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


import OpenGL.GL            as gl
import OpenGL.raw.GL._types as gltypes

import                         glvolume_funcs
import                         glvector_funcs


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

    vertUniforms = []
    vertAtts     = ['vertex', 'voxCoord', 'texCoord']

    glvector_funcs.compileShaders(self, vertAtts, vertUniforms)


def updateShaderState(self):
    """Updates all shader program variables. """

    opts = self.displayOpts

    useSpline = opts.interpolation == 'spline'

    gl.glUseProgram(self.shaders)
    glvector_funcs.updateFragmentShaderState(self, useSpline=useSpline)
    gl.glUseProgram(0) 


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
