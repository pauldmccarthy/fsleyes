#!/usr/bin/env python
#
# gllinevector_funcs.py - OpenGL 1.4 functions used by the GLLineVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides functions which are used by the :class:`.GLLineVector`
class to render :class:`.Image` overlays as line vector images in an OpenGL 1.4
compatible manner.


This module uses functions in the :mod:`.gl14.glvector_funcs` module, which
contains logic used for rendering both ``GLRGBVector`` and ``GLLineVector``
instances.


A :class:`.GLLineVertices` instance is used to generate line vertices and
texture coordinates for each voxel in the image. A fragment shader (the same
as that used by the :class:`.GLRGBVector` class) is used to colour each line
according to the orientation of the underlying vector.
"""


from __future__ import division

import logging

import numpy                   as np

import OpenGL.GL               as gl

import fsl.utils.transform     as transform
import fsleyes.gl.gllinevector as gllinevector
import fsleyes.gl.resources    as glresources
from . import                     glvector_funcs


log = logging.getLogger(__name__)


def init(self):
    """Compiles and configures the vertex/fragment shader programs, generates
    line vertices, and adds some listeners to properties of the
    :class:`.LineVectorOpts` instance associated with the vector
    :class:`.Image` overlay. This involves calls to the :func:`compileShaders`,
    :func:`updateShaderState`, and :func:`updateVertices` functions.
    """

    self.shader       = None
    self.lineVertices = None

    self._vertexResourceName = '{}_{}_vertices'.format(
        type(self).__name__, id(self.vectorImage))

    compileShaders(   self)
    updateShaderState(self)
    updateVertices(   self)

    opts = self.displayOpts

    def vertexUpdate(*a):
        updateVertices(self)
        updateShaderState(self)
        self.notify()

    name = '{}_vertices'.format(self.name)

    opts.addListener('transform',   name, vertexUpdate, weak=False)
    opts.addListener('directed',    name, vertexUpdate, weak=False)
    opts.addListener('unitLength',  name, vertexUpdate, weak=False)
    opts.addListener('lengthScale', name, vertexUpdate, weak=False)
    opts.addListener('orientFlip',  name, vertexUpdate, weak=False)


def destroy(self):
    """Destroys the vertex/fragment shader programs and the
    ``GLLineVertices`` instance, and removes property listeners from the
    :class:`.LineVectorOpts` instance.
    """

    glvector_funcs.destroy(self)

    name = '{}_vertices'.format(self.name)

    self.displayOpts.removeListener('transform',   name)
    self.displayOpts.removeListener('directed',    name)
    self.displayOpts.removeListener('unitLength',  name)
    self.displayOpts.removeListener('lengthScale', name)
    self.displayOpts.removeListener('orientFlip',  name)

    glresources.delete(self._vertexResourceName)


def compileShaders(self):
    """Compiles shader programs via the
    :func:`.gl14.glvector_funcs.compileShaders` function,
    and calls the :func:`updateVertices` function.
    """
    glvector_funcs.compileShaders(self, 'gllinevector')
    updateVertices(self)


def updateVertices(self):
    """Creates/refreshes the :class:`.GLLineVertices` instance which is used to
    generate line vertices and texture coordinates. If the ``GLLineVertices``
    instance exists and is up to date (see the
    :meth:`.GLLineVertices.calculateHash` method), this function does nothing.
    """

    if self.lineVertices is None:
        self.lineVertices = glresources.get(
            self._vertexResourceName, gllinevector.GLLineVertices, self)

    if hash(self.lineVertices) != self.lineVertices.calculateHash(self):

        log.debug('Re-generating line vertices '
                  'for {}'.format(self.vectorImage))

        self.lineVertices.refresh(self)
        glresources.set(self._vertexResourceName,
                        self.lineVertices,
                        overwrite=True)


def updateShaderState(self):
    """Updates all fragment/vertex shader program variables.  The fragment
    shader is configured by the
    :func:`.gl21.glvector_funcs.updateFragmentShaderState` function.
    """

    image = self.vectorImage

    glvector_funcs.updateShaderState(self)

    shape    = list(image.shape[:3])
    invShape = [1.0 / s for s in shape] + [0]
    offset   = [0.5, 0.5, 0.5, 0.0]

    self.shader.load()

    self.shader.setVertParam('invImageShape', invShape)
    self.shader.setVertParam('voxelOffsets',  offset)

    self.shader.unload()

    return True


def preDraw(self):
    """Initialises the GL state ready for drawing the :class:`.GLLineVector`.
    """
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    self.shader.load()


def draw(self, zpos, xform=None, bbox=None):
    """Draws the line vertices corresponding to a 2D plane located
    at the specified Z location.
    """

    opts                = self.displayOpts
    vertices, voxCoords = self.lineVertices.getVertices(zpos, self, bbox=bbox)

    if vertices.size == 0:
        return

    self.shader.setAttr('voxCoord', voxCoords)
    self.shader.loadAtts()

    v2d = opts.getTransform('voxel', 'display')

    if xform is None: xform = v2d
    else:             xform = transform.concat(xform, v2d)

    gl.glPushMatrix()
    gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('F'))

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)

    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size // 3)

    gl.glPopMatrix()


def drawAll(self, zposes, xforms):
    """Draws line vertices corresponding to each Z location. """
    for zpos, xform in zip(zposes, xforms):
        draw(self, zpos, xform)


def postDraw(self):
    """Clears the GL state after drawing the :class:`.GLLineVector`. """
    self.shader.unload()
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
