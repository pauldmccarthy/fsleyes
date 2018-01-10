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

import numpy               as np
import OpenGL.GL           as gl

import fsl.utils.transform as transform
import fsleyes.gl.routines as glroutines
import fsleyes.gl.shaders  as shaders
import fsleyes.gl.glvolume as glvolume


log = logging.getLogger(__name__)


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`. """

    self.shader = None

    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Cleans up the shader programs."""

    if self.shader is not None:
        self.shader.destroy()
        self.shader = None


def compileShaders(self):
    """Loads the vertex/fragment shader source, and creates a
    :class:`.GLSLShader`.
    """

    if self.shader is not None:
        self.shader.destroy()

    if self.threedee: prefix = 'glvolume_3d'
    else:             prefix = 'glvolume'

    vertSrc = shaders.getVertexShader(  prefix)
    fragSrc = shaders.getFragmentShader(prefix)

    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def updateShaderState(self):
    """Updates the parameters used by the shader programs, reflecting the
    current display properties.
    """

    if not self.ready():
        return

    opts    = self.opts
    display = self.display
    shader  = self.shader

    # The clipping range options are in the voxel value
    # range, but the shader needs them to be in image
    # texture value range (0.0 - 1.0). So let's scale
    # them.
    imageIsClip = opts.clipImage is None
    imgXform    = self.imageTexture.invVoxValXform
    if imageIsClip: clipXform = imgXform
    else:           clipXform = self.clipTexture.invVoxValXform

    clipLow    = opts.clippingRange[0] * clipXform[0, 0] + clipXform[0, 3]
    clipHigh   = opts.clippingRange[1] * clipXform[0, 0] + clipXform[0, 3]
    texZero    = 0.0                   * imgXform[ 0, 0] + imgXform[ 0, 3]
    imageShape = self.image.shape[:3]

    if imageIsClip: clipImageShape = imageShape
    else:           clipImageShape = opts.clipImage.shape[:3]

    # Create a single transformation matrix
    # which transforms from image texture values
    # to voxel values, and scales said voxel
    # values to colour map texture coordinates.
    img2CmapXform = transform.concat(
        self.colourTexture.getCoordinateTransform(),
        self.imageTexture.voxValXform)

    shader.load()

    changed = False

    changed |= shader.set('useSpline',        opts.interpolation == 'spline')
    changed |= shader.set('imageShape',       imageShape)
    changed |= shader.set('clipLow',          clipLow)
    changed |= shader.set('clipHigh',         clipHigh)
    changed |= shader.set('texZero',          texZero)
    changed |= shader.set('invertClip',       opts.invertClipping)
    changed |= shader.set('useNegCmap',       opts.useNegativeCmap)
    changed |= shader.set('imageIsClip',      imageIsClip)
    changed |= shader.set('img2CmapXform',    img2CmapXform)
    changed |= shader.set('clipImageShape',   clipImageShape)

    changed |= shader.set('imageTexture',     0)
    changed |= shader.set('colourTexture',    1)
    changed |= shader.set('negColourTexture', 2)
    changed |= shader.set('clipTexture',      3)

    if self.threedee:

        blendFactor = (1 - opts.blendFactor) ** 2
        clipPlanes  = np.zeros((opts.numClipPlanes, 4), dtype=np.float32)
        d2tmat      = opts.getTransform('display', 'texture')

        if   opts.clipMode == 'intersection': clipMode = 1
        elif opts.clipMode == 'union':        clipMode = 2
        elif opts.clipMode == 'complement':   clipMode = 3
        else:                                 clipMode = 0

        for i in range(opts.numClipPlanes):
            origin, normal   = self.get3DClipPlane(i)
            origin           = transform.transform(origin, d2tmat)
            normal           = transform.transformNormal(normal, d2tmat)
            clipPlanes[i, :] = glroutines.planeEquation2(origin, normal)

        changed |= shader.set('numClipPlanes', opts.numClipPlanes)
        changed |= shader.set('clipMode',      clipMode)
        changed |= shader.set('clipPlanes',    clipPlanes, opts.numClipPlanes)
        changed |= shader.set('blendFactor',   blendFactor)
        changed |= shader.set('stepLength',    1.0 / opts.getNumSteps())
        changed |= shader.set('alpha',         display.alpha / 100.0)

    shader.unload()

    return changed


def preDraw(self, xform=None, bbox=None):
    """Sets up the GL state to draw a slice from the given :class:`.GLVolume`
    instance.
    """
    self.shader.load()

    if isinstance(self, glvolume.GLVolume):
        clipCoordXform = self.calculateClipCoordTransform()
        self.shader.set('clipCoordXform', clipCoordXform)


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws the specified 2D slice from the specified image on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image
                  to be drawn.

    :arg zpos:    World Z position of slice to be drawn.

    :arg axes:    x, y, z axis indices.

    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.

    :arg bbox:    An optional bounding box.
    """

    vertices, voxCoords, texCoords = self.generateVertices2D(
        zpos, axes, bbox=bbox)

    if xform is not None:
        vertices = transform.transform(vertices, xform)

    self.shader.setAtt('vertex',   vertices)
    self.shader.setAtt('voxCoord', voxCoords)
    self.shader.setAtt('texCoord', texCoords)

    self.shader.loadAtts()

    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


def draw3D(self, xform=None, bbox=None):
    """Draws the image in 3D on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image
                  to be drawn.

    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.

    :arg bbox:    An optional bounding box.
    """

    opts                           = self.opts
    tex                            = self.renderTexture1
    proj                           = self.canvas.projectionMatrix
    vertices, voxCoords, texCoords = self.generateVertices3D(bbox)
    rayStep , texform              = opts.calculateRayCastSettings(xform, proj)

    if xform is not None:
        vertices = transform.transform(vertices, xform)

    self.shader.set(   'tex2ScreenXform', texform)
    self.shader.set(   'rayStep',         rayStep)
    self.shader.setAtt('vertex',          vertices)
    self.shader.setAtt('texCoord',        texCoords)

    self.shader.loadAtts()

    tex.bindAsRenderTarget()
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 36)
    tex.unbindAsRenderTarget()

    self.shader.unloadAtts()
    self.shader.unload()


def drawAll(self, axes, zposes, xforms):
    """Draws all of the specified slices. """

    nslices   = len(zposes)
    vertices  = np.zeros((nslices * 6, 3), dtype=np.float32)
    voxCoords = np.zeros((nslices * 6, 3), dtype=np.float32)
    texCoords = np.zeros((nslices * 6, 3), dtype=np.float32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):

        v, vc, tc = self.generateVertices2D(zpos, axes)
        vertices[ i * 6: i * 6 + 6, :] = transform.transform(v, xform)
        voxCoords[i * 6: i * 6 + 6, :] = vc
        texCoords[i * 6: i * 6 + 6, :] = tc

    self.shader.setAtt('vertex',   vertices)
    self.shader.setAtt('voxCoord', voxCoords)
    self.shader.setAtt('texCoord', texCoords)

    self.shader.loadAtts()

    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6 * nslices)


def postDraw(self, xform=None, bbox=None):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """
    self.shader.unloadAtts()
    self.shader.unload()

    if self.threedee:
        self.drawClipPlanes(xform=xform)
