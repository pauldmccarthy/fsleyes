#!/usr/bin/env python
#
# gllinevector_funcs.py - OpenGL 1.4 functions used by the GLLineVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides functions which are used by the :class:`.GLLineVector`
class to render :class:`.Image` overlays as line vector images in an OpenGL 1.4
compatible manner.


A :class:`.GLLineVertices` instance is used to generate line vertices and
texture coordinates for each voxel in the image. A fragment shader (the same
as that used by the :class:`.GLRGBVector` class) is used to colour each line
according to the orientation of the underlying vector.
"""


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
    """Compiles and configures the vertex/fragment shader programs, generates
    line vertices, and adds some listeners to properties of the
    :class:`.LineVectorOpts` instance associated with the vector
    :class:`.Image` overlay. This involves calls to the :func:`compileShaders`,
    :func:`updateShaderState`, and :func:`updateVertices` functions.
    """

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
    """Destroys the vertex/fragment shader programs and the
    ``GLLineVertices`` instance, and removes property listeners from the
    :class:`.LineVectorOpts` instance.
    """
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    name = '{}_vertices'.format(self.name)

    self.displayOpts.removeListener('transform',  name)
    self.displayOpts.removeListener('resolution', name)
    self.displayOpts.removeListener('directed',   name)

    glresources.delete(self._vertexResourceName)


def compileShaders(self):
    """Compiles the vertex/fragment shader programs used to draw the
    :class:`.GLLineVector` instance. This also results in a call to
    :func:`updateVertices`.
    """
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
    """Creates/refreshes the :class:`.GLLineVertices` instance which is used to
    generate line vertices and texture coordinates. If the ``GLLineVertices``
    instance exists and is up to date (see the
    :meth:`.GLLineVertices.calculateHash` method), this function does nothing.
    """
    
    image = self.image

    if self.lineVertices is None:
        self.lineVertices = glresources.get(
            self._vertexResourceName, gllinevector.GLLineVertices, self) 

    if hash(self.lineVertices) != self.lineVertices.calculateHash(self):

        log.debug('Re-generating line vertices for {}'.format(image))
        self.lineVertices.refresh(self)
        glresources.set(self._vertexResourceName,
                        self.lineVertices,
                        overwrite=True)


def updateShaderState(self):
    """Updates all fragment/vertex shader program variables. """
    
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
    """Initialises the GL state ready for drawing the :class:`.GLLineVector`.
    """
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
    """Draws the line vertices corresponding to a 2D plane located
    at the specified Z location.
    """

    display             = self.display
    opts                = self.displayOpts
    vertices, texCoords = self.lineVertices.getVertices(zpos, self)

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
    """Draws line vertices corresponding to each Z location. """
    for zpos, xform in zip(zposes, xforms):
        draw(self, zpos, xform)


def postDraw(self):
    """Clears the GL state after drawing the :class:`.GLLineVector`. """    
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    if self.display.softwareMode:
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
