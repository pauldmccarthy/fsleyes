#!/usr/bin/env python
#
# glmesh_funcs.py - OpenGL 1.4 functions used by the GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLMesh`
class to render :class:`.TriangleMesh` overlays in an OpenGL 1.4 compatible
manner.

An :class:`.ARBPShader` is used to manage the ``glmesh`` vertex/fragment
programs.
"""


import OpenGL.GL as gl

import fsl.utils.transform as transform
import fsleyes.gl.shaders  as shaders


def compileShaders(self):
    """Loads the ``glmesh`` vertex and fragment shader program source,
    and creates an :class:`.ARBPShader` instance.
    """

    if self.shader is not None:
        self.shader.destroy()

    vertSrc = shaders.getVertexShader(  'glmesh')
    fragSrc = shaders.getFragmentShader('glmesh')

    textures = {
        'cmap'    : 0,
        'negCmap' : 1
    }

    self.shader = shaders.ARBPShader(vertSrc, fragSrc, textures) 


def destroy(self):
    """Deletes the vertex/fragment shader programs that were compiled by
    :func:`compileShaders`.
    """
    if self.shader is not None:
        self.shader.destroy()

    self.shader = None 


def updateShaderState(self):
    """Updates the state of the vertex/fragment shaders according to the 
    current :class:`.MeshOpts` configuration. This involves setting the 
    parameter values used by the shaders.
    """
    self.shader.load()

    opts       = self.opts
    useNegCmap = (not opts.useLut) and opts.useNegativeCmap

    if opts.useLut:
        delta     = 1.0 / (opts.lut.max() + 1)
        cmapXform = transform.scaleOffsetXform(delta, 0.5 * delta)
    else:
        cmapXform = self.cmapTexture.getCoordinateTransform() 

    settings = [-1 if useNegCmap          else 1,
                -1 if opts.invertClipping else 1,
                opts.clippingRange.xlo,
                opts.clippingRange.xhi]

    self.shader.setFragParam('settings',  settings)
    self.shader.setFragParam('cmapXform', cmapXform)

    self.shader.unload() 


def drawColouredOutline(self, vertices, vdata):
    """Called when :attr:`.MeshOpts.outline` is ``True``, and
    :attr:`.MeshOpts.vertexData` is not ``None``. Loads and runs the
    shader program.

    :arg vertices: ``(n, 3)`` array containing the line vertices to draw.
    :arg vdata:    ``(n, )`` array containing data for each vertex.
    """

    self.shader.load()

    self.shader.setAttr('vertexData', vdata.reshape(-1, 1))

    self.shader.loadAtts()

    if self.opts.useLut:
        self.lutTexture.bindTexture(gl.GL_TEXTURE0)
    else:
        self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
        self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices.ravel('C'))
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.shape[0])
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    
    self.shader.unloadAtts()
    self.shader.unload()

    if self.opts.useLut:
        self.lutTexture.unbindTexture()
    else:
        self.cmapTexture   .unbindTexture()
        self.negCmapTexture.unbindTexture() 
