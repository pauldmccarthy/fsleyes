#!/usr/bin/env python
#
# glmodel_funcs.py - OpenGL 1.4 functions used by the GLModel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLModel`
class to render :class:`.Model` overlays in an OpenGL 1.4 compatible manner.

An :class:`.ARBPShader` is used to manage the ``glmodel`` vertex/fragment
programs.
"""


import fsl.fsleyes.gl.shaders as shaders


def compileShaders(self):
    """Loads the ``glmodel`` vertex and fragment shader program source,
    and creates a :class:`.ARBPShader` instance.
    """
    
    vertSrc  = shaders.getVertexShader(  'glmodel')
    fragSrc  = shaders.getFragmentShader('glmodel')

    textures = {'renderTexture' : 0}

    self.shader = shaders.ARBPShader(vertSrc, fragSrc, textures)


def destroy(self):
    """Deletes the vertex/fragment shader programs that were compiled by
    :func:`compileShaders`.
    """
    self.shader.delete()
    self.shader = None


def updateShaders(self):
    """Updates the state of the vertex/fragment shaders. This involves
    setting the parameter values used by the shaders.
    """ 
    offsets = self.getOutlineOffsets()
    
    loadShaders(self)
    self.shader.setFragParam('offsets', list(offsets) + [0, 0])
    unloadShaders(self)


def loadShaders(self):
    """Loads the :class:`.GLModel` vertex/fragment shader programs. """
    self.shader.load()

    
def unloadShaders(self):
    """Un-loads the :class:`.GLModel` vertex/fragment shader programs. """
    self.shader.unload() 
