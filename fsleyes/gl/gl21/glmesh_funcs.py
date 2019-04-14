#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 2.1 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.Mesh` overlays in an OpenGL 2.1 compatible
manner.

A :class:`.GLSLShader` is used to manage the ``glmesh`` vertex/fragment
shader programs.
"""


import OpenGL.GL as gl

import fsleyes.gl.shaders as shaders


def compileShaders(self):
    """Loads the ``glmesh`` vertex/fragment shader source and creates
    :class:`.GLSLShader` instance(s).
    """

    if self.threedee:

        flatVertSrc = shaders.getVertexShader(  'glmesh_3d_flat')
        flatFragSrc = shaders.getFragmentShader('glmesh_3d_flat')
        dataVertSrc = shaders.getVertexShader(  'glmesh_3d_data')
        dataFragSrc = shaders.getFragmentShader('glmesh_3d_data')

        self.flatShader = shaders.GLSLShader(flatVertSrc,
                                             flatFragSrc,
                                             indexed=True)
        self.dataShader = shaders.GLSLShader(dataVertSrc,
                                             dataFragSrc,
                                             indexed=True)

    else:

        vertSrc = shaders.getVertexShader(  'glmesh_2d_data')
        fragSrc = shaders.getFragmentShader('glmesh_2d_data')

        self.dataShader = shaders.GLSLShader(vertSrc, fragSrc)


def updateShaderState(self, **kwargs):
    """Updates the shader program according to the current :class:`.MeshOpts``
    configuration.
    """

    dopts    = self.opts
    copts    = self.canvas.opts
    vdata    = dopts.getVertexData()
    dshader  = self.dataShader
    fshader  = self.flatShader

    dshader.load()
    dshader.set('cmap',           0)
    dshader.set('negCmap',        1)
    dshader.set('useNegCmap',     kwargs['useNegCmap'])
    dshader.set('cmapXform',      kwargs['cmapXform'])
    dshader.set('flatColour',     kwargs['flatColour'])
    dshader.set('invertClip',     dopts.invertClipping)
    dshader.set('discardClipped', dopts.discardClipped)
    dshader.set('clipLow',        dopts.clippingRange.xlo)
    dshader.set('clipHigh',       dopts.clippingRange.xhi)

    if self.threedee:
        dshader.set('lighting', copts.light)
        dshader.set('lightPos', kwargs['lightPos'])

        dshader.setAtt('vertex', self.vertices)
        dshader.setAtt('normal', self.normals)

        if vdata is not None:

            vdata = vdata[:, dopts.vertexDataIndex]

            dshader.setAtt('vertexData', vdata.ravel('C'))
        dshader.setIndices(self.indices)

    dshader.unload()

    if self.threedee:
        fshader.load()
        fshader.set('lighting', copts.light)
        fshader.set('lightPos', kwargs['lightPos'])
        fshader.set('colour',   kwargs['flatColour'])

        fshader.setAtt('vertex', self.vertices)
        fshader.setAtt('normal', self.normals)
        fshader.setIndices(self.indices)
        fshader.unload()


def preDraw(self):
    """Must be called before :func:`draw`. Loads the appropriate shader
    program.
    """

    flat = self.opts.vertexData is None

    if flat: shader = self.flatShader
    else:    shader = self.dataShader

    self.activeShader = shader
    shader.load()


def draw(self,
         glType,
         vertices,
         indices=None,
         normals=None,
         vdata=None):
    """Called for 3D meshes, and when :attr:`.MeshOpts.vertexData` is not
    ``None``. Loads and runs the shader program.

    :arg glType:   The OpenGL primitive type.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.

    :arg indices:  Indices into the ``vertices`` array. If not provided,
                   ``glDrawArrays`` is used.

    :arg normals:  Vertex normals.

    :arg vdata:    ``(n, )`` array containing data for each vertex.
    """

    shader = self.activeShader

    # for 3D, shader attributes are
    # configured in updateShaderState
    if self.threedee:
        vertices = None
        normals  = None
        vdata    = None

    if vertices is not None: shader.setAtt('vertex',     vertices)
    if normals  is not None: shader.setAtt('normal',     normals)
    if vdata    is not None: shader.setAtt('vertexData', vdata)

    shader.loadAtts()

    if indices is None:
        gl.glDrawArrays(glType, 0, vertices.shape[0])
    else:
        nverts = indices.shape[0]
        if self.threedee:
            indices = None
        gl.glDrawElements(glType, nverts, gl.GL_UNSIGNED_INT, indices)


def postDraw(self):
    """Must be called after :func:`draw`. Unloads shaders, and unbinds
    textures.
    """

    shader = self.activeShader
    shader.unloadAtts()
    shader.unload()
    self.activeShader = None
