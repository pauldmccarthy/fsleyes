#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 1.4 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.Mesh` overlays in an OpenGL 1.4 compatible
manner.

An :class:`.ARBPShader` is used to manage the ``glmesh`` vertex/fragment
programs.
"""


import OpenGL.GL as gl

import fsl.utils.transform as transform

import fsleyes.gl.shaders  as shaders
import fsleyes.gl.routines as glroutines


def compileShaders(self):
    """Loads the ``glmesh`` vertex and fragment shader program source,
    and creates :class:`.ARBPShader` instance(s).
    """

    textures = {
        'cmap'    : 0,
        'negCmap' : 1
    }

    shaderDir = shaders.getShaderDir()

    if self.threedee:

        flatVertSrc = shaders.getVertexShader(  'glmesh_3d_flat')
        flatFragSrc = shaders.getFragmentShader('glmesh_3d_flat')
        dataVertSrc = shaders.getVertexShader(  'glmesh_3d_data')
        dataFragSrc = shaders.getFragmentShader('glmesh_3d_data')

        self.flatShader = shaders.ARBPShader(flatVertSrc,
                                             flatFragSrc,
                                             shaderDir)
        self.dataShader = shaders.ARBPShader(dataVertSrc,
                                             dataFragSrc,
                                             shaderDir,
                                             textures)

    else:

        vertSrc = shaders.getVertexShader(  'glmesh_2d_data')
        fragSrc = shaders.getFragmentShader('glmesh_2d_data')

        self.dataShader = shaders.ARBPShader(vertSrc, fragSrc, shaderDir)


def updateShaderState(self, **kwargs):
    """Updates the state of the vertex/fragment shaders according to the
    current :class:`.MeshOpts` configuration. This involves setting the
    parameter values used by the shaders.
    """
    dopts   = self.opts
    copts   = self.canvas.opts
    dshader = self.dataShader
    fshader = self.flatShader

    settings   = [-1 if     kwargs['useNegCmap'] else 1,
                  -1 if     dopts.invertClipping else 1,
                  -1 if not dopts.discardClipped else 1,
                  0]

    clipping   = [dopts.clippingRange.xlo, dopts.clippingRange.xhi, 0, 0]

    if self.threedee:

        lighting = list(kwargs['lightPos'])

        if copts.light: lighting += [ 1]
        else:           lighting += [-1]


    dshader.load()

    dshader.setFragParam('settings',    settings)
    dshader.setFragParam('clipping',    clipping)
    dshader.setFragParam('flatColour',  kwargs['flatColour'])
    dshader.setFragParam('cmapXform',   kwargs['cmapXform'])

    if self.threedee:
        dshader.setFragParam('lighting', lighting)

    dshader.unload()

    if self.threedee:
        fshader.load()
        fshader.setFragParam('lighting', lighting)
        fshader.setFragParam('colour',   kwargs['flatColour'])
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
    """Called for 3D meshes, and :attr:`.MeshOpts.vertexData` is not
    ``None``. Loads and runs the shader program.


    :arg glType:   The OpenGL primitive type.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.

    :arg indices:  Indices into the ``vertices`` array. If not provided,
                   ``glDrawArrays`` is used.

    :arg normals:  Vertex normals.

    :arg vdata:    ``(n, )`` array containing data for each vertex.
    """

    shader = self.activeShader

    if normals is not None: shader.setAtt('normal',     normals)
    if vdata   is not None: shader.setAtt('vertexData', vdata.reshape(-1, 1))

    if normals is not None:

        # NOTE You are assuming here that the canvas
        #      view matrix is the GL model view matrix.
        normalMatrix = self.canvas.viewMatrix
        normalMatrix = transform.invert(normalMatrix).T

        shader.setVertParam('normalMatrix', normalMatrix)

    shader.loadAtts()

    nvertices = vertices.shape[0]
    vertices  = vertices.ravel('C')

    with glroutines.enabled((gl.GL_VERTEX_ARRAY)):
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

        if indices is None:
            gl.glDrawArrays(glType, 0, nvertices)
        else:
            gl.glDrawElements(glType,
                              indices.shape[0],
                              gl.GL_UNSIGNED_INT,
                              indices.ravel('C'))


def postDraw(self):
    """Must be called after :func:`draw`. Unloads shaders, and unbinds
    textures.
    """

    shader = self.activeShader
    shader.unloadAtts()
    shader.unload()
    self.activeShader = None
