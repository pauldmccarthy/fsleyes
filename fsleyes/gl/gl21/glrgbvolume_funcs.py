#!/usr/bin/env python
#
# glrgbvolume_funcs.py - Functions used by the GLRGBVolume class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the :class:`.GLRGBVolume` class
for rendering RGB(A) :class:`.Image` overlays in an OpenGL 2.1 environment.
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

    constants = {
        'textureIs2D' : self.imageTexture.ndim == 2
    }

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, constants=constants)


def updateShaderState(self):
    """Updates all shader program variables. """

    if not self.ready():
        return

    display     = self.display
    opts        = self.opts
    image       = self.image
    shader      = self.shader
    imageShape  = image.shape[:3]
    nvals       = self.imageTexture.nvals
    texShape    = self.imageTexture.shape[:3]
    brightness  = display.brightness / 100
    contrast    = display.contrast   / 100
    rc, gc, bc  = self.channelColours()
    colourXform = fslcmaps.briconToScaleOffset(brightness, contrast, 1)
    hasAlpha    = not (nvals == 3 or opts.suppressA)

    if len(texShape) == 2:
        texShape = list(texShape) + [1]

    with shader.loaded():
        changed  = False
        changed |= shader.set('imageTexture',  0)
        changed |= shader.set('imageShape',    imageShape)
        changed |= shader.set('texShape',      texShape)
        changed |= shader.set('rcolour',       rc)
        changed |= shader.set('gcolour',       gc)
        changed |= shader.set('bcolour',       bc)
        changed |= shader.set('colourXform',   colourXform)
        changed |= shader.set('useSpline',     opts.interpolation == 'spline')
        changed |= shader.set('hasAlpha',      hasAlpha)

    return changed


def draw2D(self, *args, **kawrgs):
    """Draws a 2D slice at the given ``zpos``. Uses the
    :func:`.gl21.glvolume_funcs.draw2D` function.
    """
    with self.shader.loaded():
        glvolume_funcs.draw2D(self, *args, **kawrgs)


def drawAll(self, *args, **kawrgs):
    """Draws all specified slices. Uses the
    :func:`.gl21.glvolume_funcs.drawAll` function.
    """
    with self.shader.loaded():
        glvolume_funcs.drawAll(self, *args, **kawrgs)
