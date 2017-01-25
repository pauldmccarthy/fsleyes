#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 1.4 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.TriangleMesh` overlays in an OpenGL 1.4 compatible
manner.

An :class:`.ARBPShader` is used to manage the ``glmesh`` vertex/fragment
programs.
"""


import fsleyes.gl.shaders as shaders


def compileShaders(self):
    """Loads the ``glmesh`` vertex and fragment shader program source,
    and creates a :class:`.ARBPShader` instance.
    """
    
    vertSrc  = shaders.getVertexShader(  'glmesh')
    fragSrc  = shaders.getFragmentShader('glmesh')

    textures = {'renderTexture' : 0}

    self.shader = shaders.ARBPShader(vertSrc, fragSrc, textures)


def destroy(self):
    """Deletes the vertex/fragment shader programs that were compiled by
    :func:`compileShaders`.
    """
    self.shader.destroy()
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
    """Loads the :class:`.GLMesh` vertex/fragment shader programs. """
    self.shader.load()

    
def unloadShaders(self):
    """Un-loads the :class:`.GLMesh` vertex/fragment shader programs. """
    self.shader.unload() 
