#!/usr/bin/env python
#
# glrgbvolume_funcs.py - Functions used by the GLRGBVolume class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the :class:`.GLRGBVolume` class
for rendering RGB(A) :class:`.Image` overlays.
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

    constants = {
        'textureIs2D' : self.imageTexture.ndim == 2
    }

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, constants=constants)


def updateShaderState(self):
    """Updates all shader program variables. """

    if not self.ready():
        return

    display    = self.display
    opts       = self.opts
    image      = self.image
    shader     = self.shader
    nvals      = len(image.dtype)
    imageShape = image.shape[:3]
    texShape   = self.imageTexture.shape[:3]

    if len(texShape) == 2:
        texShape = list(texShape) + [1]

    shader.load()

    colourAdjust = fslcmaps.briconToScaleOffset(
        display.brightness / 100, display.contrast / 100, 1)

    changed  = False
    changed |= shader.set('imageTexture',  0)
    changed |= shader.set('imageShape',    imageShape)
    changed |= shader.set('texShape',      texShape)
    changed |= shader.set('alpha',         display.alpha / 100)
    changed |= shader.set('colourAdjust',  colourAdjust)
    changed |= shader.set('useSpline',     opts.interpolation == 'spline')
    changed |= shader.set('nvals',         nvals)
    shader.unload()

    return changed


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws a 2D slice at the given ``zpos``. Uses the
    :func:`.glvolume_funcs.draw2D` function.
    """
    self.shader.load()
    glvolume_funcs.draw2D(self, zpos, axes, xform, bbox)
    self.shader.unloadAtts()
    self.shader.unload()


def drawAll(self, axes, zposes, xforms):
    """Draws all specified slices. Uses the
    :func:`.glvolume_funcs.drawAll` function.
    """
    self.shader.load()
    glvolume_funcs.drawAll(self, axes, zposes, xforms)
    self.shader.unloadAtts()
    self.shader.unload()
