#!/usr/bin/env python
#
# gllinevector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                       as np
import OpenGL.GL                   as gl
import OpenGL.raw.GL._types        as gltypes

import fsl.utils.transform         as transform
import fsl.fsleyes.gl.resources    as glresources
import fsl.fsleyes.gl.routines     as glroutines
import fsl.fsleyes.gl.gllinevector as gllinevector
import fsl.fsleyes.gl.shaders      as shaders


log = logging.getLogger(__name__)


def init(self):
    
    self.shaders            = None
    self.vertexBuffer       = gl.glGenBuffers(1)
    self.texCoordBuffer     = gl.glGenBuffers(1)
    self.vertexIDBuffer     = gl.glGenBuffers(1)
    self.lineVertices       = None

    # False -> hardware shaders are in use
    # True  -> software shaders are in use
    self.swShadersInUse = False

    self._vertexResourceName = '{}_{}_vertices'.format(
        type(self).__name__, id(self.image))

    opts = self.displayOpts

    def vertexUpdate(*a):
        
        updateVertices(self)
        self.updateShaderState()
        self.onUpdate()

    name = '{}_vertices'.format(self.name)

    opts.addListener('transform',  name, vertexUpdate, weak=False)
    opts.addListener('resolution', name, vertexUpdate, weak=False)
    opts.addListener('directed',   name, vertexUpdate, weak=False)

    compileShaders(   self)
    updateShaderState(self)

    
def destroy(self):
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexIDBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.texCoordBuffer))
    gl.glDeleteProgram(self.shaders)

    name = '{}_vertices'.format(self.name)
    self.displayOpts.removeListener('transform',  name)
    self.displayOpts.removeListener('resolution', name)
    self.displayOpts.removeListener('directed',   name)

    if self.display.softwareMode:
        glresources.delete(self._vertexResourceName)


def compileShaders(self):
    
    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)
    
    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.swShadersInUse     = self.display.softwareMode

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
    self.cmapXformPos       = gl.glGetUniformLocation(self.shaders,
                                                      'cmapXform')
    
    updateVertices(self)

    
def updateShaderState(self):
    
    display = self.display
    opts    = self.displayOpts

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

    if not display.softwareMode:
        
        directed  = opts.directed
        imageDims = self.image.pixdim[:3]
        d2vMat    = opts.getTransform('display', 'voxel')
        v2dMat    = opts.getTransform('voxel',   'display')

        imageDims = np.array(imageDims, dtype=np.float32)
        d2vMat    = np.array(d2vMat,    dtype=np.float32).ravel('C')
        v2dMat    = np.array(v2dMat,    dtype=np.float32).ravel('C')

        gl.glUniform1f( self.directedPos,     directed)
        gl.glUniform3fv(self.imageDimsPos, 1, imageDims)

        gl.glUniformMatrix4fv(self.displayToVoxMatPos, 1, False, d2vMat)
        gl.glUniformMatrix4fv(self.voxToDisplayMatPos, 1, False, v2dMat) 

    gl.glUseProgram(0) 


def updateVertices(self):

    image   = self.image
    display = self.display
    opts    = self.displayOpts

    if not display.softwareMode:

        self.lineVertices = None
        
        if glresources.exists(self._vertexResourceName):
            log.debug('Clearing any cached line vertices for {}'.format(image))
            glresources.delete(self._vertexResourceName)
        return

    if self.lineVertices is None:
        self.lineVertices = glresources.get(
            self._vertexResourceName, gllinevector.GLLineVertices, self)
    
    newHash = (hash(opts.transform)  ^
               hash(opts.resolution) ^
               hash(opts.directed))

    if hash(self.lineVertices) != newHash:

        log.debug('Re-generating line vertices for {}'.format(image))
        self.lineVertices.refresh(self)
        glresources.set(self._vertexResourceName,
                        self.lineVertices,
                        overwrite=True)


def preDraw(self):
    gl.glUseProgram(self.shaders)


def draw(self, zpos, xform=None):
    if self.display.softwareMode: softwareDraw(self, zpos, xform)
    else:                         hardwareDraw(self, zpos, xform)


def softwareDraw(self, zpos, xform=None):

    # Software shaders have not yet been compiled - 
    # we can't draw until they're updated
    if not self.swShadersInUse:
        return

    opts                = self.displayOpts
    vertices, texCoords = self.lineVertices.getVertices(self, zpos)

    if vertices.size == 0:
        return
    
    vertices  = vertices .ravel('C')
    texCoords = texCoords.ravel('C')

    v2d = opts.getTransform('voxel', 'display')

    if xform is None: xform = v2d
    else:             xform = transform.concat(v2d, xform)
 
    gl.glPushMatrix()
    gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('C'))

    # upload the vertices
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        self.vertexPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    gl.glEnableVertexAttribArray(self.vertexPos)

    # and the texture coordinates
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.texCoordBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, texCoords.nbytes, texCoords, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        self.texCoordPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    gl.glEnableVertexAttribArray(self.texCoordPos) 
        
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size / 3)

    gl.glPopMatrix()
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glDisableVertexAttribArray(self.vertexPos)


def hardwareDraw(self, zpos, xform=None):

    if self.swShadersInUse:
        return

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

    for zpos, xform in zip(zposes, xforms):
        self.draw(zpos, xform)


def postDraw(self):
    gl.glUseProgram(0)
