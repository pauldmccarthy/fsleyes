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

    self._vertexResourceName = '{}_{}_vertices'.format(
        type(self).__name__, id(self.image))

    opts = self.displayOpts

    def vertexUpdate(*a):
        
        self.updateShaderState()
        self.onUpdate()

    name = '{}_vertices'.format(self.name)

    opts.addListener('transform',  name, vertexUpdate, weak=False)
    opts.addListener('resolution', name, vertexUpdate, weak=False)
    opts.addListener('directed',   name, vertexUpdate, weak=False)

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

    name = '{}_vertices'.format(self.name)
    self.displayOpts.removeListener('transform',  name)
    self.displayOpts.removeListener('resolution', name)
    self.displayOpts.removeListener('directed',   name)


def compileShaders(self):
    """Compiles the vertex/fragment shaders, and stores references to all
    shader variables as attributes of the :class:`.GLLineVector`.
    """
    
    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)
    
    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.vertexPos          = gl.glGetAttribLocation( self.shaders,
                                                      'vertex')
    self.vertexIDPos        = gl.glGetAttribLocation( self.shaders,
                                                      'vertexID')
    self.texCoordPos        = gl.glGetAttribLocation( self.shaders,
                                                      'texCoord') 
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                      'imageShape')
    self.imageDimsPos       = gl.glGetUniformLocation(self.shaders,
                                                      'imageDims') 
    self.directedPos        = gl.glGetUniformLocation(self.shaders,
                                                      'directed')
    self.imageTexturePos    = gl.glGetUniformLocation(self.shaders,
                                                      'imageTexture')
    self.modTexturePos      = gl.glGetUniformLocation(self.shaders,
                                                      'modTexture')
    self.xColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'xColourTexture')
    self.yColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'yColourTexture') 
    self.zColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'zColourTexture')
    self.modThresholdPos    = gl.glGetUniformLocation(self.shaders,
                                                      'modThreshold') 
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                      'useSpline')
    self.voxValXformPos     = gl.glGetUniformLocation(self.shaders,
                                                      'voxValXform')
    self.voxToDisplayMatPos = gl.glGetUniformLocation(self.shaders,
                                                      'voxToDisplayMat') 
    self.displayToVoxMatPos = gl.glGetUniformLocation(self.shaders,
                                                      'displayToVoxMat')
    self.voxelOffsetPos     = gl.glGetUniformLocation(self.shaders,
                                                      'voxelOffset') 
    self.cmapXformPos       = gl.glGetUniformLocation(self.shaders,
                                                      'cmapXform')

    
def updateShaderState(self):
    """Updates all variables used by the vertex/fragment shaders. """
    
    opts = self.displayOpts

    # The coordinate transformation matrices for 
    # each of the three colour textures are identical,
    # so we'll just use the xColourTexture matrix
    cmapXform   = self.xColourTexture.getCoordinateTransform()
    voxValXform = self.imageTexture.voxValXform
    useSpline   = False
    imageShape  = np.array(self.image.shape[:3], dtype=np.float32)

    voxValXform = np.array(voxValXform, dtype=np.float32).ravel('C')
    cmapXform   = np.array(cmapXform,   dtype=np.float32).ravel('C')

    gl.glUseProgram(self.shaders)

    gl.glUniform1f( self.useSplinePos,     useSpline)
    gl.glUniform3fv(self.imageShapePos, 1, imageShape)
    
    gl.glUniformMatrix4fv(self.voxValXformPos, 1, False, voxValXform)
    gl.glUniformMatrix4fv(self.cmapXformPos,   1, False, cmapXform)

    gl.glUniform1f(self.modThresholdPos, opts.modThreshold / 100.0)

    gl.glUniform1i(self.imageTexturePos,   0)
    gl.glUniform1i(self.modTexturePos,     1)
    gl.glUniform1i(self.xColourTexturePos, 2)
    gl.glUniform1i(self.yColourTexturePos, 3)
    gl.glUniform1i(self.zColourTexturePos, 4)

    directed  = opts.directed
    imageDims = self.image.pixdim[:3]
    d2vMat    = opts.getTransform('display', 'voxel')
    v2dMat    = opts.getTransform('voxel',   'display')

    # The shader adds these offsets to
    # transformed voxel coordinates, so
    # it can floor them to get integer
    # voxel coordinates
    offset    = [0.5, 0.5, 0.5]

    offset    = np.array(offset,    dtype=np.float32)
    imageDims = np.array(imageDims, dtype=np.float32)
    d2vMat    = np.array(d2vMat,    dtype=np.float32).ravel('C')
    v2dMat    = np.array(v2dMat,    dtype=np.float32).ravel('C')

    gl.glUniform1f( self.directedPos,       directed)
    gl.glUniform3fv(self.imageDimsPos,   1, imageDims)
    gl.glUniform3fv(self.voxelOffsetPos, 1, offset)

    gl.glUniformMatrix4fv(self.displayToVoxMatPos, 1, False, d2vMat)
    gl.glUniformMatrix4fv(self.voxToDisplayMatPos, 1, False, v2dMat) 

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


    image      = self.image
    opts       = self.displayOpts
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
    gl.glUniformMatrix4fv(self.voxToDisplayMatPos, 1, False, xform)

    # bind the vertex ID buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexIDBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        self.vertexIDPos, 1, gl.GL_UNSIGNED_INT, gl.GL_FALSE, 0, None)
    gl.glEnableVertexAttribArray(self.vertexIDPos)

    # and the vertex buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)    
    gl.glVertexAttribPointer(
        self.vertexPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    gl.glEnableVertexAttribArray(self.vertexPos) 
    gl.glEnableVertexAttribArray(self.vertexIDPos) 
        
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size / 3)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glDisableVertexAttribArray(self.vertexPos)
    gl.glDisableVertexAttribArray(self.vertexIDPos) 


def drawAll(self, zposes, xforms):
    """Draws the line vectors at every slice specified by the Z locations. """

    for zpos, xform in zip(zposes, xforms):
        self.draw(zpos, xform)


def postDraw(self):
    """Clears the GL state after drawing. """
    gl.glUseProgram(0)
