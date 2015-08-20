#!/usr/bin/env python
#
# gllinevector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp
import OpenGL.raw.GL._types           as gltypes

import fsl.utils.transform            as transform
import fsl.fsleyes.gl.gllinevector    as gllinevector
import fsl.fsleyes.gl.resources       as glresources
import fsl.fsleyes.gl.shaders         as shaders


log = logging.getLogger(__name__)


def init(self):

    self.vertexProgram   = None
    self.fragmentProgram = None
    self.lineVertices    = None

    self._vertexResourceName = '{}_{}_vertices'.format(
        type(self).__name__, id(self.image))

    compileShaders(   self)
    updateShaderState(self)
    updateVertices(   self)

    opts = self.displayOpts

    def vertexUpdate(*a):
        updateVertices(self)
        updateShaderState(self)
        self.onUpdate()

    name = '{}_vertices'.format(self.name)

    opts.addListener('transform',  name, vertexUpdate, weak=False)
    opts.addListener('resolution', name, vertexUpdate, weak=False)
    opts.addListener('directed',   name, vertexUpdate, weak=False)


def destroy(self):
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    name = '{}_vertices'.format(self.name)

    self.displayOpts.removeListener('transform',  name)
    self.displayOpts.removeListener('resolution', name)
    self.displayOpts.removeListener('directed',   name)

    glresources.delete(self._vertexResourceName)


def compileShaders(self):
    if self.vertexProgram is not None:
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        
    if self.fragmentProgram is not None:
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 

    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram

    updateVertices(self)


def updateVertices(self):
    
    image = self.image
    opts  = self.displayOpts

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


def updateShaderState(self):
    opts = self.displayOpts

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)
    
    voxValXform  = self.imageTexture.voxValXform
    cmapXform    = self.xColourTexture.getCoordinateTransform()
    shape        = np.array(list(self.image.shape[:3]) + [0], dtype=np.float32)
    invShape     = 1.0 / shape
    modThreshold = [opts.modThreshold / 100.0, 0.0, 0.0, 0.0]

    if opts.transform in ('id', 'pixdim'): offset = [0.0, 0.0, 0.0, 0.0]
    else:                                  offset = [0.5, 0.5, 0.5, 0.0]

    # Vertex program inputs
    shaders.setVertexProgramVector(  0, invShape)
    shaders.setVertexProgramVector(  1, offset)

    # Fragment program inputs
    shaders.setFragmentProgramMatrix(0, voxValXform)
    shaders.setFragmentProgramMatrix(4, cmapXform)
    shaders.setFragmentProgramVector(8, shape)
    shaders.setFragmentProgramVector(9, modThreshold)

    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    

def preDraw(self):
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    if self.display.softwareMode:
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram) 


def draw(self, zpos, xform=None):

    display             = self.display
    opts                = self.displayOpts
    vertices, texCoords = self.lineVertices.getVertices(self, zpos)

    if vertices.size == 0:
        return

    if display.softwareMode:
        texCoords = texCoords.ravel('C')
        gl.glClientActiveTexture(gl.GL_TEXTURE0)
        gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, texCoords)

    vertices = vertices.ravel('C')
    v2d      = opts.getTransform('voxel', 'display')

    if xform is None: xform = v2d
    else:             xform = transform.concat(v2d, xform)
 
    gl.glPushMatrix()
    gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('C'))

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
    
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size / 3)

    gl.glPopMatrix()


def drawAll(self, zposes, xforms):
    for zpos, xform in zip(zposes, xforms):
        draw(self, zpos, xform)


def postDraw(self):
    
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    if self.display.softwareMode:
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
