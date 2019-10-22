#!/usr/bin/env python
#
# glmip_funcs.py - Functions used by GLMIP for rendering in an OpenGL 2.1
# environment.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the :class:`.GLMIP` class for
rendering in an OpenGL 2.1 environment.
"""

import numpy as np

import fsl.transform.affine as affine
import fsleyes.gl.shaders   as shaders
from . import                  glvolume_funcs


def init(self):
    """Initialise the shader programs. """
    self.shader = None
    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Destroy the shader programs. """
    self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Compiles vertex and fragment shaders. """
    if self.shader is not None:
        self.shader.destroy()

    vertSrc = shaders.getVertexShader(  'glvolume')
    fragSrc = shaders.getFragmentShader('glmip')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def updateShaderState(self):
    """Updates the vertex/fragment shader state based on the current
    state of the :class:`.MIPOpts` instance.
    """

    if not self.ready():
        return

    opts   = self.opts
    shader = self.shader

    vmin, vmax = self.overlay.dataRange

    # Convert clipping values from voxel value
    # range totexture value range (0.0 - 1.0).
    imgXform   = self.imageTexture.invVoxValXform
    clipLow    = opts.clippingRange[0] * imgXform[0, 0] + imgXform[0, 3]
    clipHigh   = opts.clippingRange[1] * imgXform[0, 0] + imgXform[0, 3]
    textureMin = vmin                  * imgXform[0, 0] + imgXform[0, 3]
    textureMax = vmax                  * imgXform[0, 0] + imgXform[0, 3]
    imageShape = self.image.shape[:3]

    # Create a single transformation matrix
    # which transforms from image texture values
    # to voxel values, and scales said voxel
    # values to colour map texture coordinates.
    img2CmapXform = affine.concat(
        self.cmapTexture.getCoordinateTransform(),
        self.imageTexture.voxValXform)

    # sqrt(3) so the window is 100%
    # along the diagonal of a cube
    window = np.sqrt(3) * opts.window / 100.0

    shader.load()

    changed = False

    changed |= shader.set('imageTexture',     0)
    changed |= shader.set('cmapTexture',      1)
    changed |= shader.set('textureMin',       textureMin)
    changed |= shader.set('textureMax',       textureMax)
    changed |= shader.set('img2CmapXform',    img2CmapXform)
    changed |= shader.set('imageShape',       imageShape)
    changed |= shader.set('useSpline',        opts.interpolation == 'spline')
    changed |= shader.set('clipLow',          clipLow)
    changed |= shader.set('clipHigh',         clipHigh)
    changed |= shader.set('invertClip',       opts.invertClipping)
    changed |= shader.set('window',           window)
    changed |= shader.set('useMinimum',       opts.minimum)
    changed |= shader.set('useAbsolute',      opts.absolute)

    shader.unload()

    return changed


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws a 2D slice at the given ``zpos``. Uses the
    :func:`.gl21.glvolume_funcs.draw2D` function.
    """
    self.shader.load()

    viewmat       = self.canvas.viewMatrix
    cdir, rayStep = self.opts.calculateRayCastSettings(viewmat)

    self.shader.set('cameraDir', cdir)
    self.shader.set('rayStep',   rayStep)

    glvolume_funcs.draw2D(self, zpos, axes, xform, bbox)
    self.shader.unloadAtts()
    self.shader.unload()
