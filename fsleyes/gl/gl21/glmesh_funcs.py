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

    self.pointShader  = shaders.GLSLShader(vertSrc, fragSrc)
    self.edgeFilter   = shaders.Filter('edge')
    self.maskFilter   = shaders.Filter('mask')
    self.smoothFilter = shaders.Filter('smooth')


def destroy(self):
    """Deletes the vertex/fragment shaders that were compiled by
    :func:`compileShaders`.
    """
    self.pointShader .destroy()
    self.edgeFilter  .destroy()
    self.maskFilter  .destroy()
    self.smoothFilter.destroy()

    self.shader       = None 
    self.edgeFilter   = None
    self.maskFilter   = None
    self.smoothFilter = None 
    
    
def loadShaders(self):
    """Loads the :class:`.GLMesh` vertex/fragment shaders. """

    self.shader.load()


def unloadShaders(self):
    """Un-loads the :class:`.GLMesh` vertex/fragment shaders. """
    self.shader.unload()
