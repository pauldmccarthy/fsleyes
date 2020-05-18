#!/usr/bin/env python
#
# gllinevector_funcs.py - OpenGL 2.1 functions used by the GLLineVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLLineVector`
class to render :class:`.Image` overlays as line vector images in an OpenGL 2.1
compatible manner.


This module uses functions in the :mod:`.gl21.glvector_funcs` module, which
contains logic used for rendering both ``GLRGBVector`` and ``GLLineVector``
instances.


The voxel coordinates for every vector are passed directly to a vertex shader
program which calculates the position of the corresponding line vertices.


The ``glvector`` fragment shader (the same as that used by the
:class:`.GLRGBVector` class) is used to colour each line according to the
orientation of the underlying vector.
"""


from __future__ import division


import logging

import numpy               as np
import OpenGL.GL           as gl

import fsl.data.constants   as constants
import fsl.transform.affine as affine
from . import                  glvector_funcs


log = logging.getLogger(__name__)


def init(self):
    """Compiles and configures the vertex/fragment shaders used to render the
    ``GLLineVector`` via calls to :func:`compileShaders` and
    :func:`updateShaderState`.
    """

    self.shader = None

    name = self.name

    compileShaders(   self)
    updateShaderState(self)

    def update(*a, **kwa):
        updateShaderState(self)
        self.notify()

    # GLVector.addListener adds a listener
    # for the transform property, so we
    # overwrite it here - we need to update
    # the display<->voxel transformation
    # matrices whenever the transform
    # changes.
    self.opts.addListener('orientFlip',  name, update, weak=False)
    self.opts.addListener('directed',    name, update, weak=False)
    self.opts.addListener('unitLength',  name, update, weak=False)
    self.opts.addListener('lengthScale', name, update, weak=False)
    self.opts.addListener('transform',
                          name,
                          update,
                          overwrite=True,
                          weak=False)


def destroy(self):
    """Deletes the vertex/fragment shaders. """

    self.opts.removeListener('orientFlip',  self.name)
    self.opts.removeListener('directed',    self.name)
    self.opts.removeListener('unitLength',  self.name)
    self.opts.removeListener('lengthScale', self.name)
    self.opts.removeListener('transform',   self.name)

    self.shader.destroy()


def compileShaders(self):
    """Compiles the vertex/fragment shaders via the
    :func:`.gl21.glvector_funcs.compileShaders` function.
    """

    self.shader = glvector_funcs.compileShaders(self, 'gllinevector')


def updateShaderState(self):
    """Updates all variables used by the vertex/fragment shaders. The fragment
    shader is configured by the
    :func:`.gl21.glvector_funcs.updateFragmentShaderState` function.
    """

    shader = self.shader
    shader.load()

    changed     = glvector_funcs.updateShaderState(self)
    image       = self.vectorImage
    opts        = self.opts

    # see comments in gl21/glvector_funcs.py
    if self.vectorImage.niftiDataType == constants.NIFTI_DT_RGB24:
        vvxMat = affine.scaleOffsetXform(2, -1)
    else:
        vvxMat = self.imageTexture.voxValXform

    directed    = opts.directed
    unitLength  = opts.unitLength
    lengthScale = opts.lengthScale / 100.0
    imageDims   = image.pixdim[:3]
    d2vMat      = opts.getTransform('display', 'voxel')
    v2dMat      = opts.getTransform('voxel',   'display')
    xFlip       = opts.orientFlip

    changed |= shader.set('vectorTexture',   4)
    changed |= shader.set('displayToVoxMat', d2vMat)
    changed |= shader.set('voxToDisplayMat', v2dMat)
    changed |= shader.set('voxValXform',     vvxMat)
    changed |= shader.set('imageDims',       imageDims)
    changed |= shader.set('directed',        directed)
    changed |= shader.set('unitLength',      unitLength)
    changed |= shader.set('lengthScale',     lengthScale)
    changed |= shader.set('xFlip',           xFlip)

    shader.unload()

    return changed


def preDraw(self, xform=None, bbox=None):
    """Prepares the GL state for drawing. This amounts to loading the
    vertex/fragment shader programs.
    """
    self.shader.load()


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Draws the line vectors at a plane at the specified Z location.
    Voxel coordinates are passed to the vertex shader, which calculates
    the corresponding line vertex locations.
    """

    opts   = self.opts
    shader = self.shader
    v2dMat = opts.getTransform('voxel', 'display')

    voxels  = self.generateVoxelCoordinates2D(zpos, axes, bbox=bbox)
    voxels  = np.repeat(voxels, 2, 0)
    indices = np.arange(voxels.shape[0], dtype=np.uint32)

    if xform is None: xform = v2dMat
    else:             xform = affine.concat(xform, v2dMat)

    shader.set(   'voxToDisplayMat', xform)
    shader.setAtt('vertexID',        indices)
    shader.setAtt('voxel',           voxels)
    shader.loadAtts()

    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, voxels.size // 3)

    shader.unloadAtts()


def draw3D(self, xform=None, bbox=None):
    """Draws the line vectors in 3D space. """
    pass


def drawAll(self, axes, zposes, xforms):
    """Draws the line vectors at every slice specified by the Z locations. """

    for zpos, xform in zip(zposes, xforms):
        self.draw2D(zpos, axes, xform)


def postDraw(self, xform=None, bbox=None):
    """Clears the GL state after drawing. """
    self.shader.unload()
