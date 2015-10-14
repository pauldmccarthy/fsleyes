#!/usr/bin/env python
#
# glmodel_funcs.py - OpenGL 2.1 functions used by the GLModel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLModel`
class to render :class:`.Model` overlays in an OpenGL 2.1 compatible manner.
"""

import numpy                  as np
import OpenGL.GL              as gl

import fsl.fsleyes.gl.shaders as shaders


def compileShaders(self):
    """Compiles vertex and fragment shaders for the given :class:`.GLModel`
    instance. The shaders, and locations of uniform variables, are added
    as attributes of the instance.
    """
    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    self.shaders  = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.texPos    = gl.glGetUniformLocation(self.shaders, 'tex')
    self.offsetPos = gl.glGetUniformLocation(self.shaders, 'offsets')


def destroy(self):
    """Deletes the vertex/fragment shaders that were compiled by
    :func:`compileShaders`.
    """
    gl.glDeleteProgram(self.shaders)


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
    offsets = np.array(offsets, dtype=np.float32)

    gl.glUseProgram(self.shaders)
    gl.glUniform1i( self.texPos,    0)
    gl.glUniform2fv(self.offsetPos, 1, offsets)
    gl.glUseProgram(0)


def loadShaders(self):
    """Loads the :class:`.GLModel` vertex/fragment shaders. """
    gl.glUseProgram(self.shaders)


def unloadShaders(self):
    """Un-loads the :class:`.GLModel` vertex/fragment shaders. """
    gl.glUseProgram(0)
