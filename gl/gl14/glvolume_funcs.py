#!/usr/bin/env python
#
# glvolume_funcs.py - OpenGL 1.4 functions used by the GLVolume class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLVolume`
class to render :class:`.Image` overlays in an OpenGL 1.4 compatible manner.
"""


import logging

import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform    as transform
import fsl.fsleyes.gl.shaders as shaders


log = logging.getLogger(__name__)


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`."""

    self.vertexProgram   = None
    self.fragmentProgram = None
    
    compileShaders(   self)
    updateShaderState(self)

    
def destroy(self):
    """Deletes handles to the vertex/fragment programs."""

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))


def compileShaders(self):
    """Compiles the vertex and fragment programs used for rendering
    :class:`.GLVolume` instances. This is performed using the :mod:`.shaders`
    module. The compiled vertex and shader programs are stored as attributes
    on the ``GLVolume`` instance, called ``vertexProgram`` and
    ``framgentProgram`` respectively.
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

    
def updateShaderState(self):
    """Sets all variables required by the vertex and fragment programs. """
    opts = self.displayOpts

    # enable the vertex and fragment programs
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    # The voxValXform transformation turns
    # an image texture value into a raw
    # voxel value. The colourMapXform
    # transformation turns a raw voxel value
    # into a value between 0 and 1, suitable
    # for looking up an appropriate colour
    # in the 1D colour map texture
    voxValXform = transform.concat(self.imageTexture.voxValXform,
                                   self.colourTexture.getCoordinateTransform())
    
    # The fragment program needs to know the image shape
    shape = list(self.image.shape[:3])

    # And the clipping range, normalised
    # to the image texture value range
    invClip = 1 if opts.invertClipping else -1
    clipLo  = opts.clippingRange[0]            * \
        self.imageTexture.invVoxValXform[0, 0] + \
        self.imageTexture.invVoxValXform[3, 0]
    clipHi  = opts.clippingRange[1]            * \
        self.imageTexture.invVoxValXform[0, 0] + \
        self.imageTexture.invVoxValXform[3, 0]
    
    shaders.setVertexProgramVector(  0, shape + [0])
    
    shaders.setFragmentProgramMatrix(0, voxValXform)
    shaders.setFragmentProgramVector(4, shape + [0])
    shaders.setFragmentProgramVector(5, [clipLo, clipHi, invClip, 0])

    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB) 


def preDraw(self):
    """Prepares to draw a slice from the given :class:`.GLVolume` instance. """

    # enable drawing from a vertex array
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glClientActiveTexture(gl.GL_TEXTURE0)
    gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

    # enable the vertex and fragment programs
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)


def draw(self, zpos, xform=None):
    """Draws a slice of the image at the given Z location. """
    
    vertices, voxCoords, texCoords = self.generateVertices(zpos, xform)
    
    # Tex coords are texture 0 coords
    # Vox coords are texture 1 coords
    vertices  = np.array(vertices,  dtype=np.float32).ravel('C')
    texCoords = np.array(texCoords, dtype=np.float32).ravel('C')

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    gl.glClientActiveTexture(gl.GL_TEXTURE0)
    gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, texCoords)
    
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    
def drawAll(self, zposes, xforms):
    """Draws mutltiple slices of the given image at the given Z position,
    applying the corresponding transformation to each of the slices.
    """

    nslices   = len(zposes)
    vertices  = np.zeros((nslices * 6, 3), dtype=np.float32)
    texCoords = np.zeros((nslices * 6, 3), dtype=np.float32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):
        
        v, vc, tc = self.generateVertices(zpos, xform)
        vertices[ i * 6: i * 6 + 6, :] = v
        texCoords[i * 6: i * 6 + 6, :] = tc

    vertices  = vertices .ravel('C')
    texCoords = texCoords.ravel('C')

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    gl.glClientActiveTexture(gl.GL_TEXTURE0)
    gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, texCoords)

    gl.glDrawArrays(gl.GL_TRIANGLES, 0, nslices * 6) 


def postDraw(self):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    gl.glClientActiveTexture(gl.GL_TEXTURE0)
    gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
