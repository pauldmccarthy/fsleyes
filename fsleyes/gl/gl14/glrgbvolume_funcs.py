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
                                     shaders.getShaderDir(),
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

    shader.load()

    changed  = False
    changed |= shader.setFragParam('rcolour',     rc)
    changed |= shader.setFragParam('gcolour',     gc)
    changed |= shader.setFragParam('bcolour',     bc)
    changed |= shader.setFragParam('colourXform', colourXform)
    changed |= shader.setFragParam('hasAlpha',    hasAlpha)

    shader.unload()

    return changed


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws a 2D slice at the given ``zpos``. Uses the
    :func:`.gl14.glvolume_funcs.draw2D` function.
    """
    self.shader.load()
    self.shader.loadAtts()
    glvolume_funcs.draw2D(self, zpos, axes, xform, bbox)
    self.shader.unloadAtts()
    self.shader.unload()


def drawAll(self, axes, zposes, xforms):
    """Draws all specified slices. Uses the
    :func:`.gl14.glvolume_funcs.drawAll` function.
    """
    self.shader.load()
    self.shader.loadAtts()
    glvolume_funcs.drawAll(self, axes, zposes, xforms)
    self.shader.unloadAtts()
    self.shader.unload()
