#!/usr/bin/env python
#
# glvolume_funcs.py - OpenGL 2.1 functions used by the GLVolume class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLVolume`
class to render :class:`.Image` overlays in an OpenGL 2.1 compatible manner.

A :class:`.GLSLShader` is used to manage the ``glvolume`` vertex/fragment
shader programs.
"""


import logging

import numpy                  as np
import OpenGL.GL              as gl

import fsl.fsleyes.gl.shaders as shaders
import fsl.utils.transform    as transform


log = logging.getLogger(__name__)


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`. """

    self.shader = None
    
    compileShaders(   self)
    updateShaderState(self)
                    

def destroy(self):
    """Cleans up the shader programs."""

    self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Loads the vertex/fragment shader source, and creates a
    :class:`.GLSLShader`.
    """

    if self.shader is not None:
        self.shader.destroy()

    vertSrc = shaders.getVertexShader(  'glvolume')
    fragSrc = shaders.getFragmentShader('glvolume')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def updateShaderState(self):
    """Updates the parameters used by the shader programs, reflecting the
    current display properties.
    """

    opts   = self.displayOpts
    shader = self.shader

    # The clipping range options are in the voxel value
    # range, but the shader needs them to be in image
    # texture value range (0.0 - 1.0). So let's scale 
    # them.
    imgXform = self.imageTexture.invVoxValXform
    if opts.clipImage is None: clipXform = imgXform
    else:                      clipXform = self.clipTexture.invVoxValXform
    
    clipLow  = opts.clippingRange[0] * clipXform[0, 0] + clipXform[3, 0]
    clipHigh = opts.clippingRange[1] * clipXform[0, 0] + clipXform[3, 0]
    texZero  = 0.0                   * imgXform[ 0, 0] + imgXform[ 3, 0]

    # Create a single transformation matrix
    # which transforms from image texture values
    # to voxel values, and scales said voxel
    # values to colour map texture coordinates.
    img2CmapXform = transform.concat(
        self.imageTexture.voxValXform,
        self.colourTexture.getCoordinateTransform())

    shader.load()

    changed = False
    
    changed |= shader.set('useSpline',        opts.interpolation == 'spline')
    changed |= shader.set('imageShape',       self.image.shape[:3])
    changed |= shader.set('clipLow',          clipLow)
    changed |= shader.set('clipHigh',         clipHigh)
    changed |= shader.set('texZero',          texZero)
    changed |= shader.set('invertClip',       opts.invertClipping)
    changed |= shader.set('useNegCmap',       opts.useNegativeCmap)
    changed |= shader.set('imageIsClip',      opts.clipImage is None)
    changed |= shader.set('img2CmapXform',    img2CmapXform)

    changed |= shader.set('imageTexture',     0)
    changed |= shader.set('colourTexture',    1)
    changed |= shader.set('negColourTexture', 2)
    changed |= shader.set('clipTexture',      3)

    shader.unload()

    return changed


def preDraw(self):
    """Sets up the GL state to draw a slice from the given :class:`.GLVolume`
    instance.
    """
    self.shader.load()


def draw(self, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image 
                  to be drawn.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """

    vertices, voxCoords, texCoords = self.generateVertices(zpos, xform)

    self.shader.setAtt('vertex',   vertices)
    self.shader.setAtt('voxCoord', voxCoords)
    self.shader.setAtt('texCoord', texCoords)

    self.shader.loadAtts()

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

    self.shader.setAtt('vertex',   vertices)
    self.shader.setAtt('voxCoord', voxCoords)
    self.shader.setAtt('texCoord', texCoords)

    self.shader.loadAtts()

    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6 * nslices)


def postDraw(self):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """
    self.shader.unloadAtts()
    self.shader.unload()
