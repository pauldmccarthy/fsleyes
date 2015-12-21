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


import glvolume_funcs
import glvector_funcs


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions, and creates a GL vertex buffer for storing vertex
    information.
    """

    self.shader = None

    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Destroys the vertex buffer and vertex/fragment shaders created
    in :func:`init`.
    """
    self.shader.delete()
    self.shader = None

    
def compileShaders(self):
    """Compiles the vertex/fragment shaders used for drawing
    :class:`.GLRGBVector` instances. Stores references to the shader
    programs, and to all shader variables on the ``GLRGBVector`` instance.
    """
    self.shader = glvector_funcs.compileShaders(self)


def updateShaderState(self):
    """Updates all shader program variables. """

    opts      = self.displayOpts
    useSpline = opts.interpolation == 'spline'

    self.shader.load()
    glvector_funcs.updateFragmentShaderState(self, useSpline=useSpline)
    self.shader.unload()


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
