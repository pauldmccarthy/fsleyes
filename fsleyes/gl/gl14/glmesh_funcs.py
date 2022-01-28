#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 1.4 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.Mesh` overlays in an OpenGL 1.4 compatible
manner.
"""


import fsleyes.gl.shaders as shaders


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

        flatVertSrc    = shaders.getVertexShader(  'glmesh_2d_flat')
        flatFragSrc    = shaders.getFragmentShader('glmesh_2d_flat')
        dataVertSrc    = shaders.getVertexShader(  'glmesh_2d_data')
        dataFragSrc    = shaders.getFragmentShader('glmesh_2d_data')
        xsectcpVertSrc = shaders.getVertexShader(  'glmesh_2d_crosssection_clipplane')
        xsectcpFragSrc = shaders.getFragmentShader('glmesh_2d_crosssection_clipplane')
        xsectblVertSrc = shaders.getVertexShader(  'glmesh_2d_crosssection_blit')
        xsectblFragSrc = shaders.getFragmentShader('glmesh_2d_crosssection_blit')

        self.flatShader    = shaders.ARBPShader(flatVertSrc,    flatFragSrc)
        self.dataShader    = shaders.ARBPShader(dataVertSrc,    dataFragSrc)
        self.xsectcpShader = shaders.ARBPShader(xsectcpVertSrc, xsectcpFragSrc)
        self.xsectblShader = shaders.ARBPShader(xsectblVertSrc, xsectblFragSrc)


def updateShaderState(self, **kwargs):
    """Updates the state of the vertex/fragment shaders according to the
    current :class:`.MeshOpts` configuration. This involves setting the
    parameter values used by the shaders.
    """
    dopts      = self.opts
    dshader    = self.dataShader
    fshader    = self.flatShader
    xscpshader = self.xsectcpShader
    xsblshader = self.xsectblShader

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

    if not self.threedee:
        with xscpshader.loaded():
            xscpshader.setAtt('vertex', self.vertices)
            xscpshader.setIndices(      self.indices)
        with xsblshader.loaded():
            xsblshader.set('colour', kwargs['flatColour'])
