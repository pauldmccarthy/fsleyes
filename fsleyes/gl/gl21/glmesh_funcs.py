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

    
def updateShaderState(self):
    """Updates the shader program according to the current :class:`.MeshOpts``
    configuration.
    """
    self.shader.load()

    opts = self.opts
    
    self.shader.set('cmap',          0)
    self.shader.set('negCmap',       1)
    self.shader.set('useNegCmap',    opts.useNegativeCmap)
    self.shader.set('cmapXform',     self.cmapTexture.getCoordinateTransform())
    self.shader.set('invertClip',    opts.invertClipping)
    self.shader.set('clipLow',       self.opts.clippingRange.xlo)
    self.shader.set('clipHigh',      self.opts.clippingRange.xhi)

    self.shader.unload()

    
def drawColouredOutline(self, vertices, vdata):
    """Called when :attr:`.MeshOpts.outline` is ``True``, and
    :attr:`.MeshOpts.vertexData` is not ``None``. Loads and runs the
    shader program.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.
    :arg vdata:    ``(n, )`` array containing data for each vertex.
    """

    self.shader.load()

    self.shader.setAtt('vertexData', vdata)
    self.shader.setAtt('vertex',     vertices)

    self.shader.loadAtts()

    self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
    self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)

    gl.glDrawArrays(gl.GL_LINES, 0, vertices.shape[0])
    
    self.shader.unloadAtts()
    self.shader.unload()
    
    self.cmapTexture   .unbindTexture()
    self.negCmapTexture.unbindTexture() 
