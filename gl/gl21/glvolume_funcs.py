#!/usr/bin/env python
#
# glvolume_funcs.py - Functions used by the GLVolume class to render 3D images
#                     in an OpenGL 2.1 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A GLVolume object encapsulates the OpenGL information necessary
to render 2D slices of a 3D image, in an OpenGL 2.1 compatible manner.

This module is extremely tightly coupled to the fragment shader
program ``glvolume_frag.glsl``.

This module provides the following functions:

 - :func:`init`:              Initialises GL objects and memory buffers.

 - :func:`compileShaders`:    Compiles vertex/fragment shaders.

 - :func:`updateShaderState`: Refreshes the parameters used by the shader
                              programs, controlling clipping and interpolation.

 - :func:`preDraw`:           Prepares the GL state for drawing.

 - :func:`draw`:              Draws the scene.

 - :func:`drawAll`:           Draws multiple scenes.

 - :func:`postDraw`:          Resets the GL state after drawing.

 - :func:`destroy`:           Deletes the vertex and texture coordinate VBOs.
"""

import logging
import ctypes

import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fsleyes.gl.shaders  as shaders
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)


def compileShaders(self):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and attaches a reference to the resulting program, and
    all GLSL variables, to the given :class:`.GLVolume` object. 
    """

    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)

    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    # indices of all vertex/fragment shader parameters
    self.vertexPos          = gl.glGetAttribLocation( self.shaders,
                                                      'vertex')
    self.voxCoordPos        = gl.glGetAttribLocation( self.shaders,
                                                      'voxCoord')
    self.texCoordPos        = gl.glGetAttribLocation( self.shaders,
                                                      'texCoord') 
    self.imageTexturePos    = gl.glGetUniformLocation(self.shaders,
                                                      'imageTexture')
    self.colourTexturePos   = gl.glGetUniformLocation(self.shaders,
                                                      'colourTexture') 
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                      'imageShape')
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                      'useSpline')
    self.voxValXformPos     = gl.glGetUniformLocation(self.shaders,
                                                      'voxValXform')
    self.clipLowPos         = gl.glGetUniformLocation(self.shaders,
                                                      'clipLow')
    self.clipHighPos        = gl.glGetUniformLocation(self.shaders,
                                                      'clipHigh')
    self.invertClipPos      = gl.glGetUniformLocation(self.shaders,
                                                      'invertClip')


def init(self):
    """Compiles the vertex and fragment shaders used to render image slices.
    """

    self.shaders = None
    
    compileShaders(   self)
    updateShaderState(self)
    
    self.vertexAttrBuffer = gl.glGenBuffers(1)
                    

def destroy(self):
    """Cleans up the vertex buffer handle and shader programs."""

    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexAttrBuffer))
    gl.glDeleteProgram(self.shaders)


def updateShaderState(self):
    """Updates the parameters used by the shader programs, reflecting the
    current display properties.
    """

    opts = self.displayOpts

    gl.glUseProgram(self.shaders)
    
    # bind the current interpolation setting,
    # image shape, and image->screen axis
    # mappings
    gl.glUniform1f( self.useSplinePos,     opts.interpolation == 'spline')
    gl.glUniform3fv(self.imageShapePos, 1, np.array(self.image.shape,
                                                     dtype=np.float32))

    # The clipping range options are in the voxel value
    # range, but the shader needs them to be in image
    # texture value range (0.0 - 1.0). So let's scale 
    # them.
    xform    = self.imageTexture.invVoxValXform
    clipLow  = opts.clippingRange[0] * xform[0, 0] + xform[3, 0]
    clipHigh = opts.clippingRange[1] * xform[0, 0] + xform[3, 0]

    gl.glUniform1f(self.clipLowPos,    clipLow)
    gl.glUniform1f(self.clipHighPos,   clipHigh)
    gl.glUniform1f(self.invertClipPos, opts.invertClipping)
    
    # Bind transformation matrix to transform
    # from image texture values to voxel values,
    # and and to scale said voxel values to
    # colour map texture coordinates
    vvx = transform.concat(self.imageTexture.voxValXform,
                           self.colourTexture.getCoordinateTransform())
    vvx = np.array(vvx, dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(self.voxValXformPos, 1, False, vvx)

    # Set up the colour and image textures
    gl.glUniform1i(self.imageTexturePos,  0)
    gl.glUniform1i(self.colourTexturePos, 1)

    gl.glUseProgram(0)


def preDraw(self):
    """Sets up the GL state to draw a slice from the given :class:`.GLVolume`
    instance.
    """

    # load the shaders
    gl.glUseProgram(self.shaders)


def _prepareVertexAttributes(self, vertices, voxCoords, texCoords):
    """Prepares a data buffer which contains the given vertices,
    voxel coordinates, and texture coordinates, ready to be passed in to
    the shader programs.
    """

    buf    = np.zeros((vertices.shape[0] * 3, 3), dtype=np.float32)
    verPos = self.vertexPos
    voxPos = self.voxCoordPos
    texPos = self.texCoordPos

    # We store each of the three coordinate
    # sets in a single interleaved buffer
    buf[ ::3, :] = vertices
    buf[1::3, :] = voxCoords
    buf[2::3, :] = texCoords

    buf = buf.ravel('C')
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexAttrBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, buf.nbytes, buf, gl.GL_STATIC_DRAW)

    gl.glVertexAttribPointer(
        verPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 36, None)
    gl.glVertexAttribPointer(
        texPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 36, ctypes.c_void_p(24))

    # The sw shader does not use voxel coordinates
    # so attempting to binding would raise an error.
    # So we only attempt to bind if softwareMode is
    # false, and there is a shader uniform position
    # for the voxel coordinates available.
    if not self.display.softwareMode and voxPos != -1:
        gl.glVertexAttribPointer(
            voxPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 36, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(self.voxCoordPos)

    gl.glEnableVertexAttribArray(self.vertexPos)
    gl.glEnableVertexAttribArray(self.texCoordPos) 

    
def draw(self, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image 
                  to be drawn.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """

    vertices, voxCoords, texCoords = self.generateVertices(zpos, xform)
    _prepareVertexAttributes(self, vertices, voxCoords, texCoords)

    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


def drawAll(self, zposes, xforms):
    """Delegates to the default implementation in :meth:`.GLObject.drawAll`.
    """

    nslices   = len(zposes)
    vertices  = np.zeros((nslices * 6, 3), dtype=np.float32)
    voxCoords = np.zeros((nslices * 6, 3), dtype=np.float32)
    texCoords = np.zeros((nslices * 6, 3), dtype=np.float32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):
        
        v, vc, tc = self.generateVertices(zpos, xform)
        vertices[ i * 6: i * 6 + 6, :] = v
        voxCoords[i * 6: i * 6 + 6, :] = vc
        texCoords[i * 6: i * 6 + 6, :] = tc

    _prepareVertexAttributes(self, vertices, voxCoords, texCoords)
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6 * nslices)


def postDraw(self):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """

    gl.glDisableVertexAttribArray(self.vertexPos)
    gl.glDisableVertexAttribArray(self.texCoordPos)

    # See comments in _prepareVertexAttributes
    # about softwareMode/voxel coordinates
    if not self.display.softwareMode and self.voxCoordPos != -1:
        gl.glDisableVertexAttribArray(self.voxCoordPos)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glUseProgram(0)
