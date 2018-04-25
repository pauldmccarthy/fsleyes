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
import fsleyes.gl.routines as glroutines
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

    if self.threedee: frag = 'glvolume_3d'
    else:             frag = 'glvolume'

    vertSrc  = shaders.getVertexShader(  'glvolume')
    fragSrc  = shaders.getFragmentShader(frag)
    texes    = {
        'imageTexture'     : 0,
        'colourTexture'    : 1,
        'negColourTexture' : 2,
        'clipTexture'      : 3
    }

    constants = {'kill_fragments_early' : not self.threedee}

    if self.threedee:

        if   self.opts.clipMode == 'intersection': clipMode = 1
        elif self.opts.clipMode == 'union':        clipMode = 2
        elif self.opts.clipMode == 'complement':   clipMode = 3
        else:                                      clipMode = 0

        constants['numSteps']        = self.opts.numInnerSteps
        constants['clipMode']        = clipMode
        constants['numClipPlanes']   = self.opts.numClipPlanes
        texes[    'startingTexture'] = 4
        texes[    'depthTexture']    = 5

    self.shader = shaders.ARBPShader(vertSrc,
                                     fragSrc,
                                     shaders.getShaderDir(),
                                     texes,
                                     constants)


def updateShaderState(self):
    """Sets all variables required by the vertex and fragment programs. """

    if not self.ready():
        return

    opts   = self.opts
    shader = self.shader

    # enable the vertex and fragment programs
    shader.load()

    # The voxValXform transformation turns
    # an image texture value into a raw
    # voxel value. The colourMapXform
    # transformation turns a raw voxel value
    # into a value between 0 and 1, suitable
    # for looking up an appropriate colour
    # in the 1D colour map texture.
    voxValXform = transform.concat(self.colourTexture.getCoordinateTransform(),
                                   self.imageTexture.voxValXform)
    voxValXform = [voxValXform[0, 0], voxValXform[0, 3], 0, 0]

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

    clipping = [clipLo, clipHi, invClip, imageIsClip]
    negCmap  = [useNegCmap, texZero, 0, 0]

    changed  = False
    changed |= shader.setFragParam('voxValXform', voxValXform)
    changed |= shader.setFragParam('clipping',    clipping)
    changed |= shader.setFragParam('negCmap',     negCmap)

    if self.threedee:
        clipPlanes  = np.zeros((5, 4), dtype=np.float32)
        d2tmat      = opts.getTransform('display', 'texture')

        for i in range(opts.numClipPlanes):
            origin, normal   = self.get3DClipPlane(i)
            origin           = transform.transform(origin, d2tmat)
            normal           = transform.transformNormal(normal, d2tmat)
            clipPlanes[i, :] = glroutines.planeEquation2(origin, normal)

        changed |= shader.setFragParam('clipPlanes', clipPlanes)

    self.shader.unload()

    return changed


def preDraw(self, xform=None, bbox=None):
    """Prepares to draw a slice from the given :class:`.GLVolume` instance. """

    self.shader.load()
    self.shader.loadAtts()

    if isinstance(self, glvolume.GLVolume):
        clipCoordXform = self.calculateClipCoordTransform()
        self.shader.setVertParam('clipCoordXform', clipCoordXform)


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws a 2D slice of the image at the given Z location. """

    vertices, voxCoords, texCoords = self.generateVertices2D(
        zpos, axes, bbox=bbox)

    if xform is not None:
        vertices = transform.transform(vertices, xform)

    vertices = np.array(vertices, dtype=np.float32).ravel('C')

    # Voxel coordinates are calculated
    # in the vertex program
    self.shader.setAtt('texCoord', texCoords)

    with glroutines.enabled((gl.GL_VERTEX_ARRAY)):
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


def draw3D(self, xform=None, bbox=None):
    """Draws the image in 3D on the canvas.

    :arg self:    The :class:`.GLVolume` object which is managing the image
                  to be drawn.

    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.

    :arg bbox:    An optional bounding box.
    """
    opts    = self.opts
    canvas  = self.canvas
    display = self.display
    shader  = self.shader
    proj    = canvas.projectionMatrix
    src     = self.renderTexture1
    dest    = self.renderTexture2
    w, h    = src.getSize()

    vertices, voxCoords, texCoords = self.generateVertices3D(bbox)
    rayStep, texform               = opts.calculateRayCastSettings(xform, proj)

    if xform is not None:
        vertices = transform.transform(vertices, xform)

    vertices = np.array(vertices, dtype=np.float32).ravel('C')

    outerLoop  = opts.getNumOuterSteps()
    screenSize = [1.0 / w, 1.0 / h, 0, 0]
    rayStep    = list(rayStep)   + [0]
    texform    = texform[2, :]
    settings   = [
        (1 - opts.blendFactor) ** 2,
        0,
        0,
        display.alpha / 100.0]

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    shader.setAtt(      'texCoord',        texCoords)
    shader.setFragParam('rayStep',         rayStep)
    shader.setFragParam('screenSize',      screenSize)
    shader.setFragParam('tex2ScreenXform', texform)

    # Disable blending - we want each
    # loop to replace the contents of
    # the texture, not blend into it!
    with glroutines.enabled((gl.GL_VERTEX_ARRAY)), \
         glroutines.disabled((gl.GL_BLEND)):

        for i in range(outerLoop):

            settings    = list(settings)
            dtex        = src.depthTexture
            settings[1] = i * opts.numInnerSteps

            if i == outerLoop - 1: settings[2] =  1
            else:                  settings[2] = -1

            shader.setFragParam('settings', settings)

            dest.bindAsRenderTarget()
            src .bindTexture(gl.GL_TEXTURE4)
            dtex.bindTexture(gl.GL_TEXTURE5)

            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 36)

            src .unbindTexture()
            dtex.unbindTexture()
            dest.unbindAsRenderTarget()

            dest, src = src, dest

    shader.unloadAtts()
    shader.unload()

    self.renderTexture1 = src
    self.renderTexture2 = dest


def drawAll(self, axes, zposes, xforms):
    """Draws mutltiple slices of the given image at the given Z position,
    applying the corresponding transformation to each of the slices.
    """

    nslices   = len(zposes)
    vertices  = np.zeros((nslices * 6, 3), dtype=np.float32)
    texCoords = np.zeros((nslices * 6, 3), dtype=np.float32)
    indices   = np.arange(nslices * 6,     dtype=np.uint32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):

        v, vc, tc = self.generateVertices2D(zpos, axes)

        vertices[ i * 6: i * 6 + 6, :] = transform.transform(v, xform)
        texCoords[i * 6: i * 6 + 6, :] = tc

    vertices = vertices.ravel('C')

    self.shader.setAtt('texCoord', texCoords)

    with glroutines.enabled((gl.GL_VERTEX_ARRAY)):
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
        gl.glDrawElements(gl.GL_TRIANGLES,
                          nslices * 6,
                          gl.GL_UNSIGNED_INT,
                          indices)


def postDraw(self, xform=None, bbox=None):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """
    self.shader.unloadAtts()
    self.shader.unload()

    if self.threedee:
        self.drawClipPlanes(xform=xform)
