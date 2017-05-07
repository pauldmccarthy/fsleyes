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

import fsl.utils.transform as transform
import fsleyes.gl.shaders  as shaders


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

    opts       = self.opts
    useNegCmap = (not opts.useLut) and opts.useNegativeCmap

    if opts.useLut:
        delta     = 1.0 / (opts.lut.max() + 1)
        cmapXform = transform.scaleOffsetXform(delta, 0.5 * delta)
    else:
        cmapXform = self.cmapTexture.getCoordinateTransform()

    self.shader.set('cmap',          0)
    self.shader.set('negCmap',       1)
    self.shader.set('useNegCmap',    useNegCmap)
    self.shader.set('cmapXform',     cmapXform)
    self.shader.set('invertClip',    opts.invertClipping)
    self.shader.set('clipLow',       self.opts.clippingRange.xlo)
    self.shader.set('clipHigh',      self.opts.clippingRange.xhi)

    self.shader.unload()


def drawColouredOutline(self, vertices, vdata, indices=None, glType=None):
    """Called when :attr:`.MeshOpts.outline` is ``True``, and
    :attr:`.MeshOpts.vertexData` is not ``None``. Loads and runs the
    shader program.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.
    :arg vdata:    ``(n, )`` array containing data for each vertex.
    :arg indices:  Indices into the ``vertices`` array. If not provided,
                   ``glDrawArrays`` is used.
    :arg glType:   The OpenGL primitive type. If not provided, ``GL_LINES``
                   is assumed.
    """

    if glType is None:
        glType = gl.GL_LINES

    self.shader.load()

    self.shader.setAtt('vertexData', vdata)
    self.shader.setAtt('vertex',     vertices)

    self.shader.loadAtts()

    if self.opts.useLut:
        self.lutTexture.bindTexture(gl.GL_TEXTURE0)
    else:
        self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
        self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)

    if indices is None:
        gl.glDrawArrays(glType, 0, vertices.shape[0])
    else:
        gl.glDrawElements(glType,
                          indices.shape[0],
                          gl.GL_UNSIGNED_INT,
                          indices.ravel('C'))

    self.shader.unloadAtts()
    self.shader.unload()

    if self.opts.useLut:
        self.lutTexture.unbindTexture()
    else:
        self.cmapTexture   .unbindTexture()
        self.negCmapTexture.unbindTexture()
