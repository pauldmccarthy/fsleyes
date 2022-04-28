#!/usr/bin/env python
#
# glrgbvolume_funcs.py - GL14/GLRGBVolume functions.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the :class:`.GLRGBVolume` class
for rendering RGB(A) :class:`.Image` overlays in an OpenGL 1.4 environment.
"""


import fsleyes.colourmaps as fslcmaps
import fsleyes.gl.shaders as shaders
from . import                glvolume_funcs


def init(self):
    """Compiles and initialises the shader program. """
    self.shader = None
    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Destroys the shader program. """
    if self.shader is not None:
        self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Loads the vertex/fragment shader source code, and creates a
    :class:`.GLSLShader` program.
    """

    if self.shader is not None:
        self.shader.destroy()

    vertSrc = shaders.getVertexShader(  'glvolume')
    fragSrc = shaders.getFragmentShader('glrgbvolume')

    textures = {
        'imageTexture' : 0
    }

    constants = {
        'texture_is_2d' : self.imageTexture.ndim == 2
    }

    self.shader = shaders.ARBPShader(vertSrc,
                                     fragSrc,
                                     textureMap=textures,
                                     constants=constants)


def updateShaderState(self):
    """Updates all shader program variables. """

    if not self.ready():
        return

    display     = self.display
    opts        = self.opts
    shader      = self.shader
    nvals       = self.imageTexture.nvals
    texShape    = self.imageTexture.shape[:3]
    brightness  = display.brightness / 100
    contrast    = display.contrast   / 100
    rc, gc, bc  = self.channelColours()
    colourXform = fslcmaps.briconToScaleOffset(brightness, contrast, 1)
    hasAlpha    = [-1 if (nvals == 3 or opts.suppressA) else 1]

    if len(texShape) == 2:
        texShape = list(texShape) + [1]

    with shader.loaded():
        changed  = False
        changed |= shader.setFragParam('rcolour',     rc)
        changed |= shader.setFragParam('gcolour',     gc)
        changed |= shader.setFragParam('bcolour',     bc)
        changed |= shader.setFragParam('colourXform', colourXform)
        changed |= shader.setFragParam('hasAlpha',    hasAlpha)

    return changed


def draw2D(self, *args, **kawrgs):
    """Draws a 2D slice at the given ``zpos``. Uses the
    :func:`.gl14.glvolume_funcs.draw2D` function.
    """
    with self.shader.loaded():
        glvolume_funcs.draw2D(self, *args, **kawrgs)


def drawAll(self, *args, **kawrgs):
    """Draws all specified slices. Uses the
    :func:`.gl14.glvolume_funcs.drawAll` function.
    """
    with self.shader.loaded():
        glvolume_funcs.drawAll(self, *args, **kawrgs)
