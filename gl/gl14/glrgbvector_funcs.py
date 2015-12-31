#!/usr/bin/env python
#
# glrgbvector_funcs.py - OpenGL 1.4 functions used by the GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLRGBVector`
class to render :class:`.Image` overlays as RGB vector images in an OpenGL 1.4
compatible manner.


Rendering of a ``GLRGBVector`` is very similar to that of a
:class:`.GLVolume`; therefore, the ``preDraw``, ``draw``, ``drawAll`` and
``postDraw`` functions defined in the :mod:`.gl14.glvolume_funcs` are re-used
by this module.
"""


import glvolume_funcs
import glvector_funcs


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
    """Compiles the vertex/fragment shader programs used for drawing
    :class:`.GLRGBVector` instances. Stores references to the shader
    programs on the ``GLRGBVector`` instance. 
    """
    glvector_funcs.compileShaders(self, 'glvolume')


def updateShaderState(self):
    """Updates all variables used by the vertex/fragment shader programs. """

    glvector_funcs.updateFragmentShaderState(self)

    shape = list(self.vectorImage.shape[:3])

    self.shader.load()
    self.shader.setVertParam('imageShape', shape + [0])
    self.shader.unload()


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
