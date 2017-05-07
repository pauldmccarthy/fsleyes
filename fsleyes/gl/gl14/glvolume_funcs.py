#!/usr/bin/env python
#
# glvolume_funcs.py - OpenGL 1.4 functions used by the GLVolume class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLVolume`
class to render :class:`.Image` overlays in an OpenGL 1.4 compatible manner.

An :class:`.ARBPShader` is used to manage the ``glvolume`` vertex/fragment
programs.
"""


import logging

import numpy               as np
import OpenGL.GL           as gl

import fsl.utils.transform as transform
import fsleyes.gl.shaders  as shaders
import fsleyes.gl.glvolume as glvolume


log = logging.getLogger(__name__)


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`."""

    self.shader = None

    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Deletes handles to the vertex/fragment programs."""

    if self.shader is not None:
        self.shader.destroy()
        self.shader = None


def compileShaders(self):
    """Creates a :class:`.ARBPShader` instance. """

    if self.shader is not None:
        self.shader.destroy()

    vertSrc  = shaders.getVertexShader(  'glvolume')
    fragSrc  = shaders.getFragmentShader('glvolume')
    textures = {
        'imageTexture'     : 0,
        'colourTexture'    : 1,
        'negColourTexture' : 2,
        'clipTexture'      : 3
    }

    self.shader = shaders.ARBPShader(vertSrc, fragSrc, textures)


def updateShaderState(self):
    """Sets all variables required by the vertex and fragment programs. """

    if not self.ready():
        return

    opts = self.displayOpts

    # enable the vertex and fragment programs
    self.shader.load()

    # The voxValXform transformation turns
    # an image texture value into a raw
    # voxel value. The colourMapXform
    # transformation turns a raw voxel value
    # into a value between 0 and 1, suitable
    # for looking up an appropriate colour
    # in the 1D colour map texture
    voxValXform = transform.concat(self.colourTexture.getCoordinateTransform(),
                                   self.imageTexture.voxValXform)

    # The vertex and fragment programs
    # need to know the image shape
    shape = list(self.image.shape[:3])

    # And the clipping range, normalised
    # to the image texture value range
    invClip     = 1 if opts.invertClipping    else -1
    useNegCmap  = 1 if opts.useNegativeCmap   else  0
    imageIsClip = 1 if opts.clipImage is None else -1

    imgXform = self.imageTexture.invVoxValXform
    if opts.clipImage is None: clipXform = imgXform
    else:                      clipXform = self.clipTexture.invVoxValXform

    clipLo  = opts.clippingRange[0] * clipXform[0, 0] + clipXform[0, 3]
    clipHi  = opts.clippingRange[1] * clipXform[0, 0] + clipXform[0, 3]
    texZero = 0.0                   * imgXform[ 0, 0] + imgXform[ 0, 3]

    shape    = shape + [0]
    clipping = [clipLo, clipHi, invClip, imageIsClip]
    negCmap  = [useNegCmap, texZero, 0, 0]

    changed  = False
    changed |= self.shader.setVertParam('imageShape',     shape)
    changed |= self.shader.setFragParam('imageShape',     shape)
    changed |= self.shader.setFragParam('voxValXform',    voxValXform)
    changed |= self.shader.setFragParam('clipping',       clipping)
    changed |= self.shader.setFragParam('negCmap',        negCmap)

    self.shader.unload()

    return changed


def preDraw(self):
    """Prepares to draw a slice from the given :class:`.GLVolume` instance. """

    self.shader.load()
    self.shader.loadAtts()

    opts = self.displayOpts

    if isinstance(self, glvolume.GLVolume):
        if opts.clipImage is None:
            clipCoordXform = np.eye(4)
        else:
            clipCoordXform = transform.concat(
                self.clipOpts.getTransform('display', 'texture'),
                opts         .getTransform('texture', 'display'))

        self.shader.setVertParam('clipCoordXform', clipCoordXform)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)


def draw(self, zpos, xform=None, bbox=None):
    """Draws a slice of the image at the given Z location. """

    vertices, voxCoords, texCoords = self.generateVertices(zpos, xform, bbox)

    vertices = np.array(vertices, dtype=np.float32).ravel('C')

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    self.shader.setAttr('texCoord', texCoords)

    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


def drawAll(self, zposes, xforms):
    """Draws mutltiple slices of the given image at the given Z position,
    applying the corresponding transformation to each of the slices.
    """

    nslices   = len(zposes)
    vertices  = np.zeros((nslices * 6, 3), dtype=np.float32)
    texCoords = np.zeros((nslices * 6, 3), dtype=np.float32)
    indices   = np.arange(nslices * 6,     dtype=np.uint32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):

        v, vc, tc = self.generateVertices(zpos, xform)

        vertices[ i * 6: i * 6 + 6, :] = v
        texCoords[i * 6: i * 6 + 6, :] = tc

    vertices = vertices.ravel('C')

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    self.shader.setAttr('texCoord', texCoords)

    gl.glDrawElements(gl.GL_TRIANGLES,
                      nslices * 6,
                      gl.GL_UNSIGNED_INT,
                      indices)


def postDraw(self):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    self.shader.unloadAtts()
    self.shader.unload()
