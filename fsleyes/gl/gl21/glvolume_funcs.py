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

import numpy                as np
import OpenGL.GL            as gl

import fsl.transform.affine as affine
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.shaders   as shaders
import fsleyes.gl.glvolume  as glvolume


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

    env = {'textureIs2D' : self.imageTexture.ndim == 2}

    vertSrc = shaders.getVertexShader(  prefix)
    fragSrc = shaders.getFragmentShader(prefix)

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, constants=env)


def updateShaderState(self):
    """Updates the parameters used by the shader programs, reflecting the
    current display properties.
    """

    if not self.ready():
        return

    opts    = self.opts
    display = self.display
    shader  = self.shader

    imageIsClip = opts.clipImage     is None
    imageIsMod  = opts.modulateImage is None

    # The clipping options are in the voxel value
    # range, but the shader needs them to be in image
    # texture value range (0.0 - 1.0). So let's scale
    # them.
    imgXform = self.imageTexture.invVoxValXform
    if imageIsClip: clipXform = imgXform
    else:           clipXform = self.clipTexture.invVoxValXform
    if imageIsMod:  modXform  = imgXform
    else:           modXform  = self.modulateTexture.invVoxValXform

    modAlpha      = opts.modulateAlpha
    fullModXform  = self.getModulateValueXform()
    modScale      = fullModXform[0, 0]
    modOffset     = fullModXform[0, 3]

    clipLow    = opts.clippingRange[0] * clipXform[0, 0] + clipXform[0, 3]
    clipHigh   = opts.clippingRange[1] * clipXform[0, 0] + clipXform[0, 3]
    texZero    = 0.0                   * imgXform[ 0, 0] + imgXform[ 0, 3]
    modZero    = 0.0                   * modXform[ 0, 0] + modXform[ 0, 3]
    clipZero   = 0.0                   * clipXform[0, 0] + clipXform[0, 3]
    imageShape = self.image.shape[:3]
    texShape   = self.imageTexture.shape[:3]
    useSpline  = opts.interpolation in ('spline', 'use_spline')

    if len(texShape) == 2:
        texShape = list(texShape) + [1]

    if imageIsClip: clipImageShape = imageShape
    else:           clipImageShape = opts.clipImage.shape[:3]
    if imageIsMod:  modImageShape  = imageShape
    else:           modImageShape  = opts.modulateImage.shape[:3]

    # Create a single transformation matrix
    # which transforms from image texture values
    # to voxel values, and scales said voxel
    # values to colour map texture coordinates.
    img2CmapXform = affine.concat(
        self.cmapTexture.getCoordinateTransform(),
        self.imageTexture.voxValXform)

    shader.load()

    # disable clipimage/modalpha in 3D
    if self.threedee:
        imageIsClip = True
        imageIsMod  = True
        modAlpha    = False

    changed = False

    changed |= shader.set('useSpline',        useSpline)
    changed |= shader.set('imageShape',       imageShape)
    changed |= shader.set('texShape',         texShape)
    changed |= shader.set('clipLow',          clipLow)
    changed |= shader.set('clipHigh',         clipHigh)
    changed |= shader.set('modScale',         modScale)
    changed |= shader.set('modOffset',        modOffset)
    changed |= shader.set('texZero',          texZero)
    changed |= shader.set('modZero',          modZero)
    changed |= shader.set('clipZero',         clipZero)
    changed |= shader.set('invertClip',       opts.invertClipping)
    changed |= shader.set('useNegCmap',       opts.useNegativeCmap)
    changed |= shader.set('imageIsClip',      imageIsClip)
    changed |= shader.set('imageIsMod',       imageIsMod)
    changed |= shader.set('img2CmapXform',    img2CmapXform)
    changed |= shader.set('clipImageShape',   clipImageShape)
    changed |= shader.set('modImageShape',    modImageShape)
    changed |= shader.set('modulateAlpha',    modAlpha)
    changed |= shader.set('imageTexture',     0)
    changed |= shader.set('colourTexture',    1)
    changed |= shader.set('negColourTexture', 2)
    changed |= shader.set('clipTexture',      3)
    changed |= shader.set('modulateTexture',  4)

    if self.threedee:
        clipPlanes  = np.zeros((opts.numClipPlanes, 4), dtype=np.float32)
        d2tmat      = opts.getTransform('display', 'texture')

        if   opts.clipMode == 'intersection': clipMode = 1
        elif opts.clipMode == 'union':        clipMode = 2
        elif opts.clipMode == 'complement':   clipMode = 3
        else:                                 clipMode = 0

        for i in range(opts.numClipPlanes):
            origin, normal   = self.get3DClipPlane(i)
            origin           = affine.transform(origin, d2tmat)
            normal           = affine.transformNormal(normal, d2tmat)
            clipPlanes[i, :] = glroutines.planeEquation2(origin, normal)

        changed |= shader.set('numClipPlanes',    opts.numClipPlanes)
        changed |= shader.set('clipMode',         clipMode)
        changed |= shader.set('clipPlanes',
                              clipPlanes,
                              opts.numClipPlanes)
        changed |= shader.set('blendFactor',      opts.blendFactor)
        changed |= shader.set('blendByIntensity', opts.blendByIntensity)
        changed |= shader.set('stepLength',       1.0 / opts.getNumSteps())
        changed |= shader.set('alpha',            display.alpha / 100.0)

    shader.unload()

    return changed


def preDraw(self):
    """Sets up the GL state to draw a slice from the given :class:`.GLVolume`
    instance.
    """
    self.shader.load()

    if isinstance(self, glvolume.GLVolume) and not self.threedee:
        clipCoordXform = self.getAuxTextureXform('clip')
        modCoordXform  = self.getAuxTextureXform('modulate')
        self.shader.set('clipCoordXform', clipCoordXform)
        self.shader.set('modCoordXform',  modCoordXform)


def draw2D(self, canvas, zpos, axes, xform=None):
    """Draws the specified 2D slice from the specified image on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image
                  to be drawn.

    :arg canvas:  The canvas being drawn on

    :arg zpos:    World Z position of slice to be drawn.

    :arg axes:    x, y, z axis indices.

    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """

    shader                         = self.shader
    bbox                           = canvas.viewport
    mvpmat                         = canvas.mvpMatrix
    vertices, voxCoords, texCoords = self.generateVertices2D(
        zpos, axes, bbox=bbox)

    # We apply the MVP matrix here rather than in
    # the shader, as we're only drawing 6 vertices.
    if xform is not None:
        mvpmat = affine.concat(mvpmat, xform)

    vertices = affine.transform(vertices, mvpmat)

    shader.setAtt('vertex',   vertices)
    shader.setAtt('voxCoord', voxCoords)
    shader.setAtt('texCoord', texCoords)

    with shader.loadedAtts():
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


def draw3D(self, canvas, xform=None):
    """Draws the image in 3D on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image
                  to be drawn.

    :arg canvas:  The canvas being drawn on

    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """

    ovl     = self.overlay
    opts    = self.opts
    shader  = self.shader
    copts   = canvas.opts
    bbox    = canvas.viewport
    mvmat   = canvas.viewMatrix
    mvpmat  = canvas.mvpMatrix
    projmat = canvas.projectionMatrix
    tex     = self.renderTexture1

    # The xform, if provided, is an occlusion
    # depth offset (see Scene3DCanvas._draw).
    # We have to apply it *after* the mv
    # transform for occlusion work.
    if xform is not None:
        mvmat  = affine.concat(mvmat,  xform)
        mvpmat = affine.concat(mvpmat, xform)

    vertices, _, texCoords = self.generateVertices3D(bbox)
    rayStep , texform      = opts.calculateRayCastSettings(mvmat, projmat)

    rayStep = affine.transformNormal(
        rayStep, self.imageTexture.texCoordXform(ovl.shape))
    texform = affine.concat(
        texform, self.imageTexture.invTexCoordXform(ovl.shape))

    # If lighting is enabled, we specify the light
    # position in image texture coordinates, to make
    # life easier for the shader
    if copts.light:
        lxform   = opts.getTransform('display', 'texture')
        lightPos = affine.transform(canvas.lightPos, lxform)
    else:
        lightPos = [0, 0, 0]

    shader.set(   'lighting',        copts.light)
    shader.set(   'tex2ScreenXform', texform)
    shader.set(   'rayStep',         rayStep)
    shader.set(   'lightPos',        lightPos)
    shader.set(   'mvmat',           mvmat)
    shader.set(   'mvpmat',          mvpmat)
    shader.setAtt('vertex',          vertices)
    shader.setAtt('texCoord',        texCoords)

    with shader.loadedAtts(), tex.target():
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 36)

    shader.unload()
    self.drawClipPlanes(xform=xform)


def drawAll(self, canvas, axes, zposes, xforms):
    """Draws all of the specified slices. """

    nslices   = len(zposes)
    shader    = self.shader
    mvpmat    = canvas.mvpMatrix
    vertices  = np.zeros((nslices * 6, 3), dtype=np.float32)
    voxCoords = np.zeros((nslices * 6, 3), dtype=np.float32)
    texCoords = np.zeros((nslices * 6, 3), dtype=np.float32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):

        xform     = affine.concat(mvpmat, xform)
        v, vc, tc = self.generateVertices2D(zpos, axes)
        vertices[ i * 6: i * 6 + 6, :] = affine.transform(v, xform)
        voxCoords[i * 6: i * 6 + 6, :] = vc
        texCoords[i * 6: i * 6 + 6, :] = tc

    shader.setAtt('vertex',   vertices)
    shader.setAtt('voxCoord', voxCoords)
    shader.setAtt('texCoord', texCoords)

    with shader.loadedAtts():
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6 * nslices)


def postDraw(self):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """
    self.shader.unload()
