#!/usr/bin/env python
#
# gllabel_funcs.py - OpenGL 2.1 functions used by the GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLLabel`
class to render :class:`.Image` overlays in an OpenGL 2.1 compatible manner.

Rendering of a ``GLLabel`` is very similar to that of a ``GLVolume``, with the
exception that a different fragment shader (``gllabel``) is used. The
``preDraw``, ``draw``, ``drawAll`` and ``postDraw`` functions defined in the
:mod:`.gl21.glvolume_funcs` are re-used by this module.
"""


import numpy              as np

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
    :class:`.GLSLShader` program.
    """

    if self.shader is not None:
        self.shader.destroy()

    vertSrc = shaders.getVertexShader(  'glvolume')
    fragSrc = shaders.getFragmentShader('gllabel')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def updateShaderState(self):
    """Updates all shader program variables. """

    if not self.ready():
        return

    opts   = self.opts
    shader = self.shader

    imageShape = np.array(self.image.shape[:3])
    vvx        = self.imageTexture.voxValXform

    shader.load()

    changed  = False
    changed |= shader.set('numLabels',    opts.lut.max() + 1)
    changed |= shader.set('imageShape',   imageShape)
    changed |= shader.set('voxValXform',  vvx)
    changed |= shader.set('imageTexture', 0)
    changed |= shader.set('lutTexture',   1)

    shader.unload()

    return changed


def draw2D(self, *args, **kwargs):
    """Draws the label overlay in 2D. See :meth:`.GLObject.draw2D`."""
    self.shader.load()
    glvolume_funcs.draw2D(self, *args, **kwargs)
    self.shader.unloadAtts()
    self.shader.unload()


def drawAll(self, *args, **kwargs):
    """Draws the label overlay in 2D. See :meth:`.GLObject.draw2D`."""
    self.shader.load()
    glvolume_funcs.drawAll(self, *args, **kwargs)
    self.shader.unloadAtts()
    self.shader.unload()


def draw3D(self, *args, **kwargs):
    pass
