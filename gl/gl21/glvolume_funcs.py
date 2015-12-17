#!/usr/bin/env python
#
# glvolume_funcs.py - OpenGL 2.1 functions used by the GLVolume class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLVolume`
class to render :class:`.Image` overlays in an OpenGL 2.1 compatible manner.
"""


import logging
import ctypes

import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fsleyes.gl.shaders  as shaders
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`,
    and creates a GL buffer which will be used to store vertex data.
    """

    self.shaders = None
    
    compileShaders(   self)
    updateShaderState(self)
    
    self.vertexAttrBuffer = gl.glGenBuffers(1)
                    

def destroy(self):
    """Cleans up the vertex buffer handle and shader programs."""

    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexAttrBuffer))
    gl.glDeleteProgram(self.shaders)


def compileShaders(self):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and attaches a reference to the resulting program, and
    all GLSL variables, as attributes on the given :class:`.GLVolume`
    object. 
    """

    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    shaderVars = {}

    vertAtts     = ['vertex',           'voxCoord',    'texCoord']
    fragUniforms = ['imageTexture',     'clipTexture', 'colourTexture',
                    'negColourTexture', 'imageIsClip', 'useNegCmap',
                    'imageShape',       'useSpline',   'voxValXform',
                    'clipLow',          'clipHigh',    'texZero',
                    'invertClip']

    for va in vertAtts:
        shaderVars[va] = gl.glGetAttribLocation(self.shaders, va)
        
    for fu in fragUniforms:
        if fu in shaderVars:
            continue
        shaderVars[fu] = gl.glGetUniformLocation(self.shaders, fu)

    self.shaderVars = shaderVars


def updateShaderState(self):
    """Updates the parameters used by the shader programs, reflecting the
    current display properties.
    """

    opts  = self.displayOpts
    svars = self.shaderVars

    gl.glUseProgram(self.shaders)

    # The clipping range options are in the voxel value
    # range, but the shader needs them to be in image
    # texture value range (0.0 - 1.0). So let's scale 
    # them.
    if opts.clipImage is None: xform = self.imageTexture.invVoxValXform
    else:                      xform = self.clipTexture .invVoxValXform
    
    clipLow  = opts.clippingRange[0] * xform[0, 0] + xform[3, 0]
    clipHigh = opts.clippingRange[1] * xform[0, 0] + xform[3, 0]
    texZero  = 0.0                   * xform[0, 0] + xform[3, 0]

    # Bind transformation matrix to transform
    # from image texture values to voxel values,
    # and and to scale said voxel values to
    # colour map texture coordinates
    vvx = transform.concat(self.imageTexture.voxValXform,
                           self.colourTexture.getCoordinateTransform())
    vvx = np.array(vvx, dtype=np.float32).ravel('C')


    # bind the current interpolation setting,
    # image shape, and image->screen axis
    # mappings
    gl.glUniform1f( svars['useSpline'],     opts.interpolation == 'spline')
    gl.glUniform3fv(svars['imageShape'], 1, np.array(self.image.shape,
                                                     dtype=np.float32))

    gl.glUniform1f(svars['clipLow'],     clipLow)
    gl.glUniform1f(svars['clipHigh'],    clipHigh)
    gl.glUniform1f(svars['texZero'],     texZero)
    gl.glUniform1f(svars['invertClip'],  opts.invertClipping)
    gl.glUniform1f(svars['useNegCmap'],  opts.useNegativeCmap)
    gl.glUniform1f(svars['imageIsClip'], opts.clipImage is None)
 
    gl.glUniformMatrix4fv(svars['voxValXform'], 1, False, vvx)

    # Set up the colour and image textures
    gl.glUniform1i(svars['imageTexture'],     0)
    gl.glUniform1i(svars['colourTexture'],    1)
    gl.glUniform1i(svars['negColourTexture'], 2)
    gl.glUniform1i(svars['clipTexture'],      3)

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
    verPos = self.shaderVars['vertex']
    voxPos = self.shaderVars['voxCoord']
    texPos = self.shaderVars['texCoord']

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
    gl.glVertexAttribPointer(
        voxPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 36, ctypes.c_void_p(12))
    
    gl.glEnableVertexAttribArray(voxPos)
    gl.glEnableVertexAttribArray(verPos)
    gl.glEnableVertexAttribArray(texPos) 

    
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
    """Draws all of the specified slices. """

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

    gl.glDisableVertexAttribArray(self.shaderVars['vertex'])
    gl.glDisableVertexAttribArray(self.shaderVars['texCoord'])
    gl.glDisableVertexAttribArray(self.shaderVars['voxCoord'])
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glUseProgram(0)
