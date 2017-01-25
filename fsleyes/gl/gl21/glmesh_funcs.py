#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 2.1 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.TriangleMesh` overlays in an OpenGL 2.1 compatible
manner.

A :class:`.GLSLShader` is used to manage the ``glmesh`` vertex/fragment
shader programs.
"""


import fsleyes.gl.shaders as shaders


def compileShaders(self):
    """Loads the ``glmesh`` vertex/fragment shader source and creates a
    :class:`.GLSLShader` instance.
    """

    if self.shader is not None:
        self.shader.destroy()
    
    vertSrc = shaders.getVertexShader(  'glmesh')
    fragSrc = shaders.getFragmentShader('glmesh')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def destroy(self):
    """Deletes the vertex/fragment shaders that were compiled by
    :func:`compileShaders`.
    """
    self.shader.destroy()
    self.shader = None


def updateShaders(self):
    """Updates the state of the vertex/fragment shaders. This involves
    setting the uniform variable values used by the shaders.
    """

    offsets = self.getOutlineOffsets()

    self.shader.load()
    self.shader.set('tex',     0)
    self.shader.set('offsets', offsets)
    self.shader.unload()


def loadShaders(self):
    """Loads the :class:`.GLMesh` vertex/fragment shaders. """

    self.shader.load()


def unloadShaders(self):
    """Un-loads the :class:`.GLMesh` vertex/fragment shaders. """
    self.shader.unload()
