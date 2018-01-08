#!/usr/bin/env python
#
# gllabel_funcs.py - OpenGL 1.4 functions used by the GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLLabel`
class to render :class:`.Image` overlays in an OpenGL 1.4 compatible manner.


Rendering of a ``GLLabel`` is very similar to that of a :class:`.GLVolume`,
with the exception that a different fragment program (``gllabel``) is used.
Therefore, the ``preDraw``, ``draw``, ``drawAll`` and ``postDraw`` functions
defined in the :mod:`.gl14.glvolume_funcs` are re-used by this module.
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
    """Deletes handles to the vertex/fragment shader programs. """
    self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Loads vertex and fragment shader program source, and creates an
    :class:`.ARBPShader` instance.
    """
    if self.shader is not None:
        self.shader.destroy()

    vertSrc  = shaders.getVertexShader(  'glvolume')
    fragSrc  = shaders.getFragmentShader('gllabel')
    textures = {
        'imageTexture' : 0,
        'lutTexture'   : 1,
    }

    self.shader = shaders.ARBPShader(vertSrc,
                                     fragSrc,
                                     shaders.getShaderDir(),
                                     textures)


def updateShaderState(self):
    """Updates all shader program variables. """

    if not self.ready():
        return

    opts = self.opts

    self.shader.load()

    voxValXform  = self.imageTexture.voxValXform
    voxValXform  = [voxValXform[0, 0], voxValXform[0, 3], 0, 0]
    invNumLabels = 1.0 / (opts.lut.max() + 1)

    self.shader.setFragParam('voxValXform',  voxValXform)
    self.shader.setFragParam('invNumLabels', [invNumLabels, 0, 0, 0])

    self.shader.unload()

    return True


def draw2D(self, *args, **kwargs):
    """Draws the label overlay in 2D. See :meth:`.GLObject.draw2D`. """
    self.shader.load()
    self.shader.loadAtts()
    glvolume_funcs.draw2D(self, *args, **kwargs)
    self.shader.unloadAtts()
    self.shader.unload()


def drawAll(self, *args, **kwargs):
    """Draws the label overlay in 2D. See :meth:`.GLObject.draw2D`. """
    self.shader.load()
    self.shader.loadAtts()
    glvolume_funcs.drawAll(self, *args, **kwargs)
    self.shader.unloadAtts()
    self.shader.unload()


def draw3D(self, *args, **kwargs):
    pass
