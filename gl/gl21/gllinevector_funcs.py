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


import logging

import numpy                   as np
import OpenGL.GL               as gl

import fsl.utils.transform     as transform
import fsl.fsleyes.gl.routines as glroutines
import                            glvector_funcs


log = logging.getLogger(__name__)


def init(self):
    """Compiles and configures the vertex/fragment shaders used to render the
    ``GLLineVector`` via calls to :func:`compileShaders` and
    :func:`updateShaderState.
    """
    
    self.shader = None

    compileShaders(   self)
    updateShaderState(self)

    
def destroy(self):
    """Deletes the vertex/fragment shaders. """
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
    
    glvector_funcs.updateFragmentShaderState(self)

    image = self.vectorImage
    opts  = self.displayOpts

    vvxMat     = self.imageTexture.voxValXform
    directed   = opts.directed
    imageDims  = image.pixdim[:3]
    d2vMat     = opts.getTransform('display', 'voxel')
    v2dMat     = opts.getTransform('voxel',   'display')

    # The shader adds these offsets to
    # transformed voxel coordinates, so
    # it can floor them to get integer
    # voxel coordinates
    offset = [0.5, 0.5, 0.5]

    shader.set('vectorTexture',   0)
    shader.set('displayToVoxMat', d2vMat)
    shader.set('voxToDisplayMat', v2dMat)
    shader.set('voxValXform',     vvxMat)
    shader.set('voxelOffset',     offset)
    shader.set('imageDims',       imageDims)
    shader.set('directed',        directed)

    shader.unload()


def preDraw(self):
    """Prepares the GL state for drawing. This amounts to loading the
    vertex/fragment shader programs.
    """
    self.shader.load()


def draw(self, zpos, xform=None):
    """Draws the line vectors at a plane at the specified Z location.
    Voxel coordinates are passed to the vertex shader, which calculates
    the corresponding line vertex locations.
    """ 

    image      = self.vectorImage
    opts       = self.displayOpts
    shader     = self.shader
    v2dMat     = opts.getTransform('voxel', 'display')
    resolution = [opts.resolution] * 3

    if opts.transform == 'id':
        resolution = resolution / min(image.pixdim[:3])
    elif opts.transform == 'pixdim':
        resolution = map(lambda r, p: max(r, p), resolution, image.pixdim[:3])

    vertices = glroutines.calculateSamplePoints(
        image.shape,
        resolution,
        v2dMat,
        self.xax,
        self.yax)[0]
    
    vertices[:, self.zax] = zpos

    vertices = np.repeat(vertices, 2, 0)
    indices  = np.arange(vertices.shape[0], dtype=np.uint32)

    if xform is None: xform = v2dMat
    else:             xform = transform.concat(v2dMat, xform)

    shader.set(   'voxToDisplayMat', xform)
    shader.setAtt('vertexID',        indices)
    shader.setAtt('vertex',          vertices)
    shader.loadAtts()
    
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size / 3)

    shader.unloadAtts()


def drawAll(self, zposes, xforms):
    """Draws the line vectors at every slice specified by the Z locations. """

    for zpos, xform in zip(zposes, xforms):
        self.draw(zpos, xform)


def postDraw(self):
    """Clears the GL state after drawing. """
    self.shader.unload()
