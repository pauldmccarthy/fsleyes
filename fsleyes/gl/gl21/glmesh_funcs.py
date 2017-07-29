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

    if self.flatShader is not None: self.flatShader.destroy()
    if self.dataShader is not None: self.dataShader.destroy()

    self.activeShader = None

    if not self.threedee:

        vertSrc = shaders.getVertexShader(  'glmesh_2d_data')
        fragSrc = shaders.getFragmentShader('glmesh_2d_data')

        self.dataShader = shaders.GLSLShader(vertSrc, fragSrc)

    else:
        print('todo')


def destroy(self):
    """Deletes the vertex/fragment shaders that were compiled by
    :func:`compileShaders`.
    """

    if self.flatShader is not None: self.flatShader.destroy()
    if self.dataShader is not None: self.dataShader.destroy()

    self.dataShader   = None
    self.flatShader   = None
    self.activeShader = None


def updateShaderState(self):
    """Updates the shader program according to the current :class:`.MeshOpts``
    configuration.
    """

    dshader = self.dataShader
    fshader = self.flatShader

    opts       = self.opts
    flatColour = opts.getConstantColour()
    useNegCmap = (not opts.useLut) and opts.useNegativeCmap

    if opts.useLut:
        delta     = 1.0 / (opts.lut.max() + 1)
        cmapXform = transform.scaleOffsetXform(delta, 0.5 * delta)
    else:
        cmapXform = self.cmapTexture.getCoordinateTransform()

    dshader.load()
    dshader.set('cmap',           0)
    dshader.set('negCmap',        1)
    dshader.set('useNegCmap',     useNegCmap)
    dshader.set('cmapXform',      cmapXform)
    dshader.set('flatColour',     flatColour)
    dshader.set('invertClip',     opts.invertClipping)
    dshader.set('discardClipped', opts.discardClipped)
    dshader.set('clipLow',        opts.clippingRange.xlo)
    dshader.set('clipHigh',       opts.clippingRange.xhi)

    dshader.unload()

    if fshader is not None:
        pass


def preDraw(self, xform=None, bbox=None):

    flat = self.opts.vertexData is None

    if flat: shader = self.flatShader
    else:    shader = self.dataShader

    self.activeShader = shader
    shader.load()

    if not flat:
        if self.opts.useLut:
            self.lutTexture.bindTexture(gl.GL_TEXTURE0)
        else:
            self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
            self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)


def drawWithShaders(self,
                    glType,
                    vertices,
                    indices=None,
                    normals=None,
                    vdata=None):
    """Called when :attr:`.MeshOpts.outline` is ``True``, and
    :attr:`.MeshOpts.vertexData` is not ``None``. Loads and runs the
    shader program.

    :arg glType:   The OpenGL primitive type. If not provided, ``GL_LINES``
                   is assumed.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.

    :arg indices:  Indices into the ``vertices`` array. If not provided,
                   ``glDrawArrays`` is used.

    :arg normals:  Vertex normals.

    :arg vdata:    ``(n, )`` array containing data for each vertex.
    """

    shader = self.activeShader

    shader.setAtt('vertex', vertices)

    if normals is not None: shader.setAtt('normal',     normals)
    if vdata   is not None: shader.setAtt('vertexData', vdata)

    shader.loadAtts()

    if indices is None:
        gl.glDrawArrays(glType, 0, vertices.shape[0])
    else:
        gl.glDrawElements(glType,
                          indices.shape[0],
                          gl.GL_UNSIGNED_INT,
                          indices.ravel('C'))

def postDraw(self, xform=None, bbox=None):

    shader = self.activeShader

    shader.unloadAtts()
    shader.unload()

    if self.opts.vertexData is not None:
        if self.opts.useLut:
            self.lutTexture.unbindTexture()
        else:
            self.cmapTexture   .unbindTexture()
            self.negCmapTexture.unbindTexture()
