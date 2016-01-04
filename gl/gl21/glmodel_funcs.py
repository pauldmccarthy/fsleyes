#!/usr/bin/env python
#
# glmodel_funcs.py - OpenGL 2.1 functions used by the GLModel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLModel`
class to render :class:`.Model` overlays in an OpenGL 2.1 compatible manner.

A :class:`.GLSLShader` is used to manage the ``glmodel`` vertex/fragment
shader programs.
"""


import fsl.fsleyes.gl.shaders as shaders


def compileShaders(self):
    """Loads the ``glmodel`` vertex/fragment shader source and creates a
    :class:`.GLSLShader` instance.
    """

    if self.shader is not None:
        self.shader.delete()
    
    vertSrc = shaders.getVertexShader(  'glmodel')
    fragSrc = shaders.getFragmentShader('glmodel')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def destroy(self):
    """Deletes the vertex/fragment shaders that were compiled by
    :func:`compileShaders`.
    """
    self.shader.delete()
    self.shader = None


def updateShaders(self):
    """Updates the state of the vertex/fragment shaders. This involves
    setting the uniform variable values used by the shaders.
    """

    width, height = self._renderTexture.getSize()
    outlineWidth  = self.opts.outlineWidth

    # outlineWidth is a value between 0.0 and 1.0 - 
    # we use this value so that it effectly sets the
    # outline to between 0% and 10% of the model
    # width/height (whichever is smaller)
    outlineWidth *= 10
    offsets = 2 * [min(outlineWidth / width, outlineWidth / height)]

    self.shader.load()
    self.shader.set('tex',     0)
    self.shader.set('offsets', offsets)
    self.shader.unload()


def loadShaders(self):
    """Loads the :class:`.GLModel` vertex/fragment shaders. """

    self.shader.load()


def unloadShaders(self):
    """Un-loads the :class:`.GLModel` vertex/fragment shaders. """
    self.shader.unload()
