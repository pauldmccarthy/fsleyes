#!/usr/bin/env python
#
# glmask_funcs.py - OpenGL 1.4 functions used by the GLMask class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMask`
class to render :class:`.Image` overlays in an OpenGL 1.4 compatible manner.
"""


import fsleyes.gl.shaders as shaders
from . import                glvolume_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions.
    """
    self.shader = None
    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Destroys the shader programs. """
    self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Loads the vertex/fragment shader source code, and creates a
    :class:`.ARBPShader` program.
    """

    if self.shader is not None:
        self.shader.destroy()

    vertSrc  = shaders.getVertexShader(  'glvolume')
    fragSrc  = shaders.getFragmentShader('glmask')
    textures = {
        'imageTexture' : 0,
    }

    self.shader = shaders.ARBPShader(vertSrc,
                                     fragSrc,
                                     shaders.getShaderDir(),
                                     textures)


def updateShaderState(self):
    """Updates all shader program variables. """

    if not self.ready():
        return

    opts       = self.opts
    shader     = self.shader
    colour     = self.getColour()
    threshold  = list(self.getThreshold())

    if opts.invert: threshold += [ 1, 0]
    else:           threshold += [-1, 0]

    shader.load()
    shader.setFragParam('threshold', threshold)
    shader.setFragParam('colour',    colour)
    shader.unload()

    return True


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws a 2D slice at the given ``zpos``. Uses the
    :func:`.glvolume_funcs.draw2D` function.
    """

    self.shader.load()
    self.shader.loadAtts()
    glvolume_funcs.draw2D(self, zpos, axes, xform, bbox)
    self.shader.unloadAtts()
    self.shader.unload()


def drawAll(self, axes, zposes, xforms):
    """Draws all specified slices. Uses the
    :func:`.glvolume_funcs.drawAll` function.
    """
    self.shader.load()
    self.shader.loadAtts()
    glvolume_funcs.drawAll(self, axes, zposes, xforms)
    self.shader.unloadAtts()
    self.shader.unload()
