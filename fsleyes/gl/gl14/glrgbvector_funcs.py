#!/usr/bin/env python
#
# glrgbvector_funcs.py - OpenGL 1.4 functions used by the GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLRGBVector`
class to render :class:`.Image` overlays as RGB vector images in an OpenGL 1.4
compatible manner.


This module uses functions in the :mod:`.gl14.glvector_funcs` module, which
contains logic used for rendering both ``GLRGBVector`` and ``GLLineVector``
instances.


Rendering of a ``GLRGBVector`` is very similar to that of a
:class:`.GLVolume`, with the exception that a different fragment shader
(``glvector``) may be used. Therefore, the ``preDraw``, ``draw``, ``drawAll``
and ``postDraw`` functions defined in the :mod:`.gl14.glvolume_funcs` are
re-used by this module.
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
    """Destroys the vertex/fragment shader programs created in :func:`init`.
    """
    glvector_funcs.destroy(self)


def compileShaders(self):
    """Calls the :mod:`.gl14.glvector_funcs.compileShaders` function.
    """
    glvector_funcs.compileShaders(self, 'glrgbvector')


def updateShaderState(self):
    """Updates all variables used by the vertex/fragment shader programs.  The
    fragment shader is configured by the
    :func:.gl21.glvector_funcs.updateFragmentShaderState` function.
    """

    if not self.ready():
        return

    shape = list(self.vectorImage.shape[:3])

    self.shader.load()
    glvector_funcs.updateShaderState(self)
    self.shader.setVertParam('imageShape', shape + [0])
    self.shader.unload()

    return True


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
