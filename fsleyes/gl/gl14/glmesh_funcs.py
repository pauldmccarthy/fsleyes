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


import numpy     as np
import OpenGL.GL as gl

import fsl.transform.affine as affine

import fsleyes.gl.shaders   as shaders
import fsleyes.gl.routines  as glroutines


def compileShaders(self):
    """Loads the ``glmesh`` vertex and fragment shader program source,
    and creates :class:`.ARBPShader` instance(s).
    """

    textures = {
        'cmap'    : 0,
        'negCmap' : 1
    }

    if self.threedee:

        flatVertSrc = shaders.getVertexShader(  'glmesh_3d_flat')
        flatFragSrc = shaders.getFragmentShader('glmesh_3d_flat')
        dataVertSrc = shaders.getVertexShader(  'glmesh_3d_data')
        dataFragSrc = shaders.getFragmentShader('glmesh_3d_data')

        self.flatShader = shaders.ARBPShader(flatVertSrc,
                                             flatFragSrc)
        self.dataShader = shaders.ARBPShader(dataVertSrc,
                                             dataFragSrc,
                                             textures)

    else:

        flatVertSrc = shaders.getVertexShader(  'glmesh_2d_flat')
        flatFragSrc = shaders.getFragmentShader('glmesh_2d_flat')
        dataVertSrc = shaders.getVertexShader(  'glmesh_2d_data')
        dataFragSrc = shaders.getFragmentShader('glmesh_2d_data')

        self.flatShader = shaders.ARBPShader(flatVertSrc, flatFragSrc)
        self.dataShader = shaders.ARBPShader(dataVertSrc, dataFragSrc)


def updateShaderState(self, **kwargs):
    """Updates the state of the vertex/fragment shaders according to the
    current :class:`.MeshOpts` configuration. This involves setting the
    parameter values used by the shaders.
    """
    dopts   = self.opts
    dshader = self.dataShader
    fshader = self.flatShader

    settings = [-1 if     kwargs['useNegCmap'] else 1,
                -1 if     dopts.invertClipping else 1,
                -1 if not dopts.discardClipped else 1,
                0]

    clipping = [dopts.clippingRange.xlo, dopts.clippingRange.xhi, 0, 0]
    modulate = [-1 if not dopts.modulateAlpha  else 1,
                kwargs['modScale'],
                kwargs['modOffset'],
                0]

    with dshader.loaded():
        dshader.setFragParam('settings',   settings)
        dshader.setFragParam('clipping',   clipping)
        dshader.setFragParam('modulate',   modulate)
        dshader.setFragParam('flatColour', kwargs['flatColour'])
        dshader.setFragParam('cmapXform',  kwargs['cmapXform'])

        if self.threedee:
            dshader.setIndices(self.indices)
            dshader.setAtt('vertex', self.vertices)
            dshader.setAtt('normal', self.normals)
            vdata = self.getVertexData('vertex')
            mdata = self.getVertexData('modulate')

            # if modulate data is not set,
            # we use the vertex data
            if mdata is None:
                mdata = vdata

            if vdata is not None: dshader.setAtt('vertexData',   vdata)
            if mdata is not None: dshader.setAtt('modulateData', mdata)

    with fshader.loaded():
        fshader.setFragParam('colour', kwargs['flatColour'])
        if self.threedee:
            fshader.setAtt('vertex', self.vertices)
            fshader.setAtt('normal', self.normals)
            fshader.setIndices(self.indices)


def draw(self,
         glType,
         vertices,
         indices=None,
         normals=None,
         vdata=None,
         mdata=None,
         xform=None):
    """Called for 3D meshes, and :attr:`.MeshOpts.vertexData` is not
    ``None``. Loads and runs the shader program.

    :arg glType:   The OpenGL primitive type.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.

    :arg indices:  Indices into the ``vertices`` array. If not provided,
                   ``glDrawArrays`` is used.

    :arg normals:  Vertex normals.

    :arg vdata:    ``(n, )`` array containing data for each vertex.

    :arg mdata:    ``(n, )`` array containing alpha modulation data for
                   each vertex.

    :arg xform:    Transformation matrix to apply to the vertices, in
                   addition to the canvas mvp matrix.
    """

    canvas = self.canvas
    copts  = canvas.opts
    shader = self.activeShader
    mvmat  = canvas.viewMatrix
    mvpmat = canvas.mvpMatrix

    if xform is not None:
        mvmat  = affine.concat(mvmat,  xform)
        mvpmat = affine.concat(mvpmat, xform)

    if normals is not None: shader.setAtt('normal',       normals)
    if vdata   is not None: shader.setAtt('vertexData',   vdata.reshape(-1, 1))
    if mdata   is not None: shader.setAtt('modulateData', mdata.reshape(-1, 1))

    shader.setAtt('vertex', vertices)

    if self.threedee:

        normmat = affine.invert(mvmat[:3, :3]).T
        normmat = np.hstack((normmat, np.zeros((3, 1))))

        if not copts.light:
            lighting = [0, 0, 0, -1]
        else:
            lighting = affine.transform(canvas.lightPos, mvmat)
            lighting = list(lighting) + [1]

        shader.setVertParam('mvmat',    mvmat)
        shader.setVertParam('mvpmat',   mvpmat)
        shader.setVertParam('normmat',  normmat)
        shader.setFragParam('lighting', lighting)
    else:
        shader.setVertParam('mvpmat',   mvpmat)

    nvertices = vertices.shape[0]

    if indices is None:
        gl.glDrawArrays(glType, 0, nvertices)
    else:
        gl.glDrawElements(glType,
                          indices.shape[0],
                          gl.GL_UNSIGNED_INT,
                          indices.ravel('C'))
