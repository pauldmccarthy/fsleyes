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


import os.path as op
import matplotlib.image as mplimg


import logging

import numpy               as np
import OpenGL.GL           as gl

import fsl.utils.transform as transform
import fsleyes.gl.shaders  as shaders
import fsleyes.gl.routines as glroutines
import fsleyes.gl.glvolume as glvolume
import fsleyes.gl.textures as textures


log = logging.getLogger(__name__)


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`."""

    self.shader = None

    self.innerSteps = 1

    compileShaders(   self)
    updateShaderState(self)

    if self.threedee:
        self.renderTexture1 = textures.RenderTexture(self.name, gl.GL_LINEAR, gl.GL_FLOAT)
        self.renderTexture2 = textures.RenderTexture(self.name, gl.GL_LINEAR, gl.GL_FLOAT)


def destroy(self):
    """Deletes handles to the vertex/fragment programs."""

    if self.shader is not None:
        self.shader.destroy()
        self.shader = None

    if self.threedee:
        self.renderTexture1.destroy()
        self.renderTexture2.destroy()
        self.renderTexture1 = None
        self.renderTexture2 = None


def compileShaders(self):
    """Creates a :class:`.ARBPShader` instance. """

    if self.shader is not None:
        self.shader.destroy()

    if self.threedee: frag = 'glvolume_3d'
    else:             frag = 'glvolume'

    vertSrc  = shaders.getVertexShader(  'glvolume')
    fragSrc  = shaders.getFragmentShader(frag)
    textures = {
        'imageTexture'     : 0,
        'colourTexture'    : 1,
        'negColourTexture' : 2,
        'clipTexture'      : 3
    }

    constants = {'kill_fragments_early' : not self.threedee}

    if self.threedee:
        constants['numSteps'] = self.innerSteps
        textures['startingTexture'] =  4

    self.shader = shaders.ARBPShader(vertSrc,
                                     fragSrc,
                                     shaders.getShaderDir(),
                                     textures,
                                     constants)


def updateShaderState(self):
    """Sets all variables required by the vertex and fragment programs. """

    if not self.ready():
        return

    opts    = self.opts
    display = self.display
    canvas  = self.canvas


    # enable the vertex and fragment programs
    self.shader.load()

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
    changed |= self.shader.setFragParam('voxValXform', voxValXform)
    changed |= self.shader.setFragParam('clipping',    clipping)
    changed |= self.shader.setFragParam('negCmap',     negCmap)

    if self.threedee:
        settings = [
            (1 - opts.blendFactor) ** 2,
            1.0 / opts.numSteps,
            canvas.fadeOut,
            display.alpha / 100.0]

        changed |= self.shader.setFragParam('settings',    settings)

    self.shader.unload()

    return changed


def preDraw(self, xform=None, bbox=None):
    """Prepares to draw a slice from the given :class:`.GLVolume` instance. """

    self.shader.load()
    self.shader.loadAtts()

    if isinstance(self, glvolume.GLVolume):
        clipCoordXform = self.calculateClipCoordTransform()
        self.shader.setVertParam('clipCoordXform', clipCoordXform)

    if self.threedee:
        w, h = self.canvas._getSize()

        w = int(np.ceil(w / 4.0))
        h = int(np.ceil(h / 4.0))

        for rt in [self.renderTexture1, self.renderTexture2]:
            if rt.getSize() != (w, h):
                rt.setSize(w, h)

        self.shader.setFragParam('screenSize', [1.0 / w, 1.0 / h, 0, 0])


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
    vertices, voxCoords, texCoords = self.generateVertices3D(bbox)
    rayStep, ditherDir, texform    = self.calculateRayCastSettings(xform)

    if xform is not None:
        vertices = transform.transform(vertices, xform)

    src  = self.renderTexture1
    dest = self.renderTexture2

    src.bindAsRenderTarget()
    gl.glClearColor(0, 0, 0, 0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    src.unbindAsRenderTarget()
    dest.bindAsRenderTarget()
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    dest.unbindAsRenderTarget()

    vertices  = np.array(vertices, dtype=np.float32).ravel('C')

    # gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
    self.shader.setAtt(      'texCoord',        texCoords)
    self.shader.setFragParam('ditherDir',       list(ditherDir) + [0])
    self.shader.setFragParam('tex2ScreenXform', texform[2, :])

    outerLoop = int(np.ceil(self.opts.numSteps / self.innerSteps))

    with glroutines.enabled((gl.GL_VERTEX_ARRAY)), \
         glroutines.disabled((gl.GL_BLEND, gl.GL_DEPTH_TEST)):
    # if True:

        for i in range(outerLoop):

            self.shader.setFragParam('rayStep',
                                     list(rayStep) + [i * self.innerSteps])

            dest.bindAsRenderTarget()
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            src.bindTexture(gl.GL_TEXTURE4)

            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 36)

            src.unbindTexture()
            dest.unbindAsRenderTarget()

            dest, src = src, dest

            if getattr(self, 'save_bmps', False):
                path = op.expanduser('~/output/{:02d}.png'.format(i))

                dbmp  = dest.getData()
                dbmp  = np.array(dbmp * 255, dtype=np.uint8)
                sbmp  = src.getData()
                sbmp  = np.array(sbmp * 255, dtype=np.uint8)

                mplimg.imsave(path, np.vstack((sbmp, dbmp)))


    self.shader.unloadAtts()
    self.shader.unload()

    gl.glDisable(gl.GL_CULL_FACE)
    verts = np.array([[-1, -1, 0],
                      [-1,  1, 0],
                      [ 1, -1, 0],
                      [ 1, -1, 0],
                      [-1,  1, 0],
                      [ 1,  1, 0]], dtype=np.float32)

    invproj = transform.invert(self.canvas.getProjectionMatrix())
    verts   = transform.transform(verts, invproj)

    src.draw(verts)


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

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    self.shader.setAtt('texCoord', texCoords)

    gl.glDrawElements(gl.GL_TRIANGLES,
                      nslices * 6,
                      gl.GL_UNSIGNED_INT,
                      indices)


def postDraw(self, xform=None, bbox=None):
    """Cleans up the GL state after drawing from the given :class:`.GLVolume`
    instance.
    """
    # gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    # self.shader.unloadAtts()
    # self.shader.unload()

    if self.threedee:
        self.drawClipPlanes()
