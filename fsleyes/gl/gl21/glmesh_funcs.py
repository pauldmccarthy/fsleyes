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

import OpenGL.GL as gl

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

    if self.shader is not None:
        self.shader.destroy()

    self.shader = None

    
def drawColouredOutline(self, vertices, vdata):

    self.shader.load()

    self.shader.set('cmap',          0)
    self.shader.set('cmapXform',     self.cmapTexture.getCoordinateTransform())
    self.shader.set('clipLow',       self.opts.clippingRange.xlo)
    self.shader.set('clipHigh',      self.opts.clippingRange.xhi)
    
    self.shader.setAtt('vertexData', vdata)
    self.shader.setAtt('vertex',     vertices)

    self.shader.loadAtts()

    self.cmapTexture.bindTexture(gl.GL_TEXTURE0)

    gl.glDrawArrays(gl.GL_LINES, 0, vertices.shape[0])
    
    self.shader.unloadAtts()
    self.shader.unload()
    
    self.cmapTexture.unbindTexture() 
