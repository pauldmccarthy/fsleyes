#!/usr/bin/env python
#
# glrgbvector_funcs.py - OpenGL 2.1 functions used by the GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLRGBVector`
class to render :class:`.Image` overlays as RGB vector images in an OpenGL 2.1
compatible manner.


This module uses functions in the :mod:`.gl21.glvector_funcs` module, which
contains logic used for rendering both ``GLRGBVector`` and ``GLLineVector``
instances.


Rendering of a ``GLRGBVector`` is very similar to that of a
:class:`.GLVolume`, with the exception that a different fragment shader
(``glvector``) may be used. Therefore, the ``preDraw``, ``draw2D``,
``draw3D``, ``drawAll`` and ``postDraw`` functions defined in the
:mod:`.gl21.glvolume_funcs` are re-used by this module.
"""


from . import glvolume_funcs
from . import glvector_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions.
    """

    self.shader = None

    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Destroys the vertex buffer and vertex/fragment shaders created
    in :func:`init`.
    """
    if self.shader is not None:
        self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Calls :func:`.gl21.glvector_funcs.compileShaders`. """
    self.shader = glvector_funcs.compileShaders(self, 'glrgbvector')


def updateShaderState(self):
    """Updates all shader program variables. Most of the shader
    configuration is performed by the
    :func:.gl21.glvector_funcs.updateShaderState` function.
    """

    if not self.ready():
        return

    opts      = self.opts
    useSpline = opts.interpolation in ('spline', 'true_spline')

    with self.shader.loaded():
        changed = glvector_funcs.updateShaderState(self, useSpline=useSpline)

    return changed


preDraw  = glvolume_funcs.preDraw
draw2D   = glvolume_funcs.draw2D
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
