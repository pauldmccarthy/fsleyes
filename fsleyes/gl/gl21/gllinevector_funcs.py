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
import fsleyes.gl.routines  as glroutines
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
    self.opts.addListener('lengthScale', name, update, weak=False)
    self.opts.addListener('transform',
                          name,
                          update,
                          overwrite=True,
                          weak=False)


def destroy(self):
    """Deletes the vertex/fragment shaders. """

    if self.opts is not None:
        self.opts.removeListener('orientFlip',  self.name)
        self.opts.removeListener('directed',    self.name)
        self.opts.removeListener('lengthScale', self.name)
        self.opts.removeListener('transform',   self.name)

    if self.shader is not None:
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
    image  = self.vectorImage
    opts   = self.opts

    # see comments in gl21/glvector_funcs.py
    if self.vectorImage.niftiDataType == constants.NIFTI_DT_RGB24:
        vvxMat = affine.scaleOffsetXform(2, -1)
    else:
        vvxMat = self.imageTexture.voxValXform

    directed    = opts.directed
    lengthScale = opts.lengthScale / 100.0
    imageDims   = image.pixdim[:3]
    xFlip       = opts.orientFlip

    # If the unitLength option is on, the vector
    # data will have already been scaled to have
    # length 1 (see GLLineVector.__init__). But
    # we draw vectors in two parts, from the voxel
    # centre. So we have to half the vector lengths.
    if opts.unitLength:
        lengthScale /= 2
        # We also scale the vector data by the
        # minimum voxel length, so that each
        # vector has unit length relative to
        # the voxel dimensions.
        fac          = (image.pixdim[:3] / min(image.pixdim[:3]))
        lengthScale /= fac

    with shader.loaded():
        changed  = glvector_funcs.updateShaderState(self)
        changed |= shader.set('vectorTexture',   4)
        changed |= shader.set('voxValXform',     vvxMat)
        changed |= shader.set('imageDims',       imageDims)
        changed |= shader.set('directed',        directed)
        changed |= shader.set('lengthScale',     lengthScale)
        changed |= shader.set('xFlip',           xFlip)

    return changed


def preDraw(self):
    """Prepares the GL state for drawing. This amounts to loading the
    vertex/fragment shader programs.
    """
    self.shader.load()


def draw2D(self, canvas, zpos, axes, xform=None, bbox=True):
    """Draws the line vectors at a plane at the specified Z location.
    Voxel coordinates are passed to the vertex shader, which calculates
    the corresponding line vertex locations.
    """

    opts      = self.opts
    shader    = self.shader
    lineWidth = self.normalisedLineWidth(canvas)
    mvpmat    = canvas.mvpMatrix
    v2dMat    = opts.getTransform('voxel', 'display')

    if bbox: bbox = canvas.viewport
    else:    bbox = None

    # Rotation matrix used to rotate lines
    # 90 degrees w.r.t. camera angle, so
    # the shader can position rectangle
    # corners.
    camera          = np.zeros(3)
    camera[axes[2]] = 1
    rotation        = glroutines.rotate(90, *camera)[:3, :3]

    # The shader is given voxel coordinates, and
    # generates polygon vertices within each voxel
    # (lines are drawn as rectangles formed of
    # two triangles). We do this by passing the
    # shader each voxel four times (one for each
    # corner).
    voxels = self.generateVoxelCoordinates2D(zpos, axes, bbox=bbox)

    # And we also pass it an index 0-3, so it
    # knows which corner it is working on each time.
    vertexIds = np.tile(np.arange(4, dtype=np.uint32), voxels.shape[0])

    # We use an index array for small cost savings,
    # so we only have to repeat voxel coordinates
    # four times, instead of six. Given four
    # vertices 0-3, we draw two triangles with
    # pattern 0 2 3 0 3 1
    indices        = np.arange(0, voxels.shape[0] * 4, 4, dtype=np.uint32)
    indices        = indices.repeat(6)
    indices[1::6] += 2
    indices[2::6] += 3
    # leave indices[3::6] referring to vertex 0
    indices[4::6] += 3
    indices[5::6] += 1
    voxels         = np.repeat(voxels, 4, axis=0)

    if xform is None: xform = affine.concat(mvpmat, v2dMat)
    else:             xform = affine.concat(mvpmat, xform, v2dMat)

    shader.set(   'camera',          camera)
    shader.set(   'cameraRotation',  rotation)
    shader.set(   'voxToDisplayMat', xform)
    shader.set(   'lineWidth',       lineWidth)
    shader.setAtt('vertexID',        vertexIds)
    shader.setAtt('voxel',           voxels)
    shader.setIndices(indices)
    shader.draw(gl.GL_TRIANGLES)



def drawAll(self, canvas, axes, zposes, xforms):
    """Draws line vertices corresponding to each Z location. """
    for zpos, xform in zip(zposes, xforms):
        draw2D(self, canvas, zpos, axes, xform, bbox=False)


def postDraw(self):
    """Clears the GL state after drawing. """
    self.shader.unload()
