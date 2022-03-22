#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 2.1 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.Mesh` overlays in an OpenGL 2.1 compatible
manner.
"""


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

        self.flatShader = shaders.GLSLShader(flatVertSrc, flatFragSrc)
        self.dataShader = shaders.GLSLShader(dataVertSrc, dataFragSrc)

    else:

        flatVertSrc    = shaders.getVertexShader(  'glmesh_2d_flat')
        flatFragSrc    = shaders.getFragmentShader('glmesh_2d_flat')
        dataVertSrc    = shaders.getVertexShader(  'glmesh_2d_data')
        dataFragSrc    = shaders.getFragmentShader('glmesh_2d_data')
        xsectcpVertSrc = shaders.getVertexShader(  'glmesh_2d_crosssection_clipplane')
        xsectcpFragSrc = shaders.getFragmentShader('glmesh_2d_crosssection_clipplane')
        xsectblVertSrc = shaders.getVertexShader(  'glmesh_2d_crosssection_blit')
        xsectblFragSrc = shaders.getFragmentShader('glmesh_2d_crosssection_blit')

        self.dataShader    = shaders.GLSLShader(dataVertSrc,    dataFragSrc)
        self.flatShader    = shaders.GLSLShader(flatVertSrc,    flatFragSrc)
        self.xsectcpShader = shaders.GLSLShader(xsectcpVertSrc, xsectcpFragSrc)
        self.xsectblShader = shaders.GLSLShader(xsectblVertSrc, xsectblFragSrc)


def updateShaderState(self, **kwargs):
    """Updates the shader program according to the current :class:`.MeshOpts``
    configuration.
    """

    dopts      = self.opts
    dshader    = self.dataShader
    fshader    = self.flatShader
    xscpshader = self.xsectcpShader
    xsblshader = self.xsectblShader

    with dshader.loaded():
        dshader.set('cmap',           0)
        dshader.set('negCmap',        1)
        dshader.set('useNegCmap',     kwargs['useNegCmap'])
        dshader.set('cmapXform',      kwargs['cmapXform'])
        dshader.set('flatColour',     kwargs['flatColour'])
        dshader.set('invertClip',     dopts.invertClipping)
        dshader.set('discardClipped', dopts.discardClipped)
        dshader.set('modulateAlpha',  dopts.modulateAlpha)
        dshader.set('modScale',       kwargs['modScale'])
        dshader.set('modOffset',      kwargs['modOffset'])
        dshader.set('clipLow',        dopts.clippingRange.xlo)
        dshader.set('clipHigh',       dopts.clippingRange.xhi)

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
        fshader.set('colour', kwargs['flatColour'])
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
