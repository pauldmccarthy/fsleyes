#!/usr/bin/env python
#
# gllinevector_funcs.py - OpenGL 2.1 functions used by the GLLineVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLLineVector`
class to render :class:`.Image` overlays as line vector images in an OpenGL 2.1
compatible manner.


This module uses two different techniques to render a ``GLLineVector``. The
voxel coordinates for every vector are passed directly to a vertex shader
program which calculates the position of the corresponding line vertices.


A fragment shader (the same as that used by the :class:`.GLRGBVector` class)
is used to colour each line according to the orientation of the underlying
vector.
"""


import logging

import numpy                       as np
import OpenGL.GL                   as gl
import OpenGL.raw.GL._types        as gltypes

import fsl.utils.transform         as transform
import fsl.fsleyes.gl.routines     as glroutines
import fsl.fsleyes.gl.shaders      as shaders
import                                glvector_funcs


log = logging.getLogger(__name__)


def init(self):
    """Compiles and configures the vertex/fragment shaders used to render the
    ``GLLineVector`` (via calls to :func:`compileShaders` and
    :func:`updateShaderState`), creates GL buffers for storing vertices,
    texture coordinates, and vertex IDs, and adds listeners to some properties
    of the :class:`.LineVectorOpts` instance associated with the vector
    :class:`.Image`  overlay.
    """
    
    self.shaders        = None
    self.vertexBuffer   = gl.glGenBuffers(1)
    self.texCoordBuffer = gl.glGenBuffers(1)
    self.vertexIDBuffer = gl.glGenBuffers(1)

    compileShaders(   self)
    updateShaderState(self)

    
def destroy(self):
    """Deletes the vertex/fragment shaders and the GL buffers, and
    removes property listeners from the :class:`.LineVectorOpts`
    instance.
    """
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexIDBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.texCoordBuffer))
    gl.glDeleteProgram(self.shaders)


def compileShaders(self):
    """Compiles the vertex/fragment shaders, and stores references to all
    shader variables as attributes of the :class:`.GLLineVector`.
    """

    vertAtts     = ['vertex', 'vertexID']
    vertUniforms = ['imageTexture', 'displayToVoxMat', 'voxToDisplayMat',
                    'voxelOffset',  'voxValXform',     'imageShape',
                    'directed',     'imageDims']

    glvector_funcs.compileShaders(self, vertAtts, vertUniforms)

    
def updateShaderState(self):
    """Updates all variables used by the vertex/fragment shaders. """


    gl.glUseProgram(self.shaders)
    glvector_funcs.updateFragmentShaderState(self)

    image = self.vectorImage
    opts  = self.displayOpts
    svars = self.shaderVars

    vvxMat     = self.imageTexture.voxValXform
    imageShape = np.array(image.shape[:3], dtype=np.float32)

    directed   = opts.directed
    imageDims  = image.pixdim[:3]
    d2vMat     = opts.getTransform('display', 'voxel')
    v2dMat     = opts.getTransform('voxel',   'display')

    # The shader adds these offsets to
    # transformed voxel coordinates, so
    # it can floor them to get integer
    # voxel coordinates
    offset    = [0.5, 0.5, 0.5]

    offset    = np.array(offset,    dtype=np.float32)
    imageDims = np.array(imageDims, dtype=np.float32)
    d2vMat    = np.array(d2vMat,    dtype=np.float32).ravel('C')
    v2dMat    = np.array(v2dMat,    dtype=np.float32).ravel('C')
    vvxMat    = np.array(vvxMat,    dtype=np.float32).ravel('C')
 
    gl.glUniform1i(       svars['imageTexture'],       0)
    gl.glUniformMatrix4fv(svars['displayToVoxMat'], 1, False, d2vMat)
    gl.glUniformMatrix4fv(svars['voxToDisplayMat'], 1, False, v2dMat)
    gl.glUniformMatrix4fv(svars['voxValXform'],     1, False, vvxMat)
    
    gl.glUniform3fv(svars['voxelOffset'], 1, offset)
    gl.glUniform3fv(svars['imageShape'],  1, imageShape)
    gl.glUniform3fv(svars['imageDims'],   1, imageDims)
    gl.glUniform1f( svars['directed'],       directed)

    gl.glUseProgram(0) 


def preDraw(self):
    """Prepares the GL state for drawing. This amounts to loading the
    vertex/fragment shader programs.
    """
    gl.glUseProgram(self.shaders)


def draw(self, zpos, xform=None):
    """Draws the line vectors at a plane at the specified Z location.
    Voxel coordinates are passed to the vertex shader, which calculates
    the corresponding line vertex locations.
    """ 


    image      = self.vectorImage
    opts       = self.displayOpts
    svars      = self.shaderVars
    v2dMat     = opts.getTransform('voxel', 'display')
    resolution = np.array([opts.resolution] * 3)

    if opts.transform == 'id':
        resolution = resolution / min(image.pixdim[:3])
    elif opts.transform == 'pixdim':
        resolution = map(lambda r, p: max(r, p), resolution, image.pixdim[:3])

    vertices = glroutines.calculateSamplePoints(
        image.shape,
        resolution,
        v2dMat,
        self.xax,
        self.yax)[0]
    
    vertices[:, self.zax] = zpos

    vertices = np.repeat(vertices, 2, 0)
    indices  = np.arange(vertices.shape[0], dtype=np.uint32)
    vertices = vertices.ravel('C')

    if xform is None: xform = v2dMat
    else:             xform = transform.concat(v2dMat, xform)
    
    xform = np.array(xform, dtype=np.float32).ravel('C') 
    gl.glUniformMatrix4fv(svars['voxToDisplayMat'], 1, False, xform)

    # bind the vertex ID buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexIDBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        svars['vertexID'], 1, gl.GL_UNSIGNED_INT, gl.GL_FALSE, 0, None)

    # and the vertex buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)    
    gl.glVertexAttribPointer(
        svars['vertex'], 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    gl.glEnableVertexAttribArray(svars['vertex']) 
    gl.glEnableVertexAttribArray(svars['vertexID'])
        
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size / 3)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glDisableVertexAttribArray(svars['vertexID'])
    gl.glDisableVertexAttribArray(svars['vertex'])


def drawAll(self, zposes, xforms):
    """Draws the line vectors at every slice specified by the Z locations. """

    for zpos, xform in zip(zposes, xforms):
        self.draw(zpos, xform)


def postDraw(self):
    """Clears the GL state after drawing. """
    gl.glUseProgram(0)
