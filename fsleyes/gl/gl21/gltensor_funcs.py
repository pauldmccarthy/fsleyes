#!/usr/bin/env python
#
# gltensor_funcs.py - OpenGL2.1 functions used by the GLTensor class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLTensor`
class for rendering :class:`.DTIFitTensor` overlays, and compatible
:class:`.Image` overlays in an OpenGL 2.1 compatible manner.


The rendering code makes use of the OpenGL ``ARB_draw_instanced`` extension
so that voxel coordinates do not need to be repeated for every vertex of
a single tensor.


For each voxel, the vertices of a unit sphere are passed to the ``gltensor``
vertex shader, which looks up the eigenvectors and values for the voxel, and
transforms the sphere accordingly.


If the :attr:`.VectorOpts.colourImage` property is not set, the ``glvector``
fragment shader is used to colour the tensors. Otherwise, the ``glvolume``
fragment shader is used to colour the tensors according to the specified
``colourImage``. The functions in the :mod:`.gl21.glvector_funcs` module
are used to manage the fragment shader.
"""


import numpy                        as np
import numpy.linalg                 as npla
import OpenGL.GL                    as gl
import OpenGL.GL.ARB.draw_instanced as arbdi

import fsl.utils.transform  as transform
import fsleyes.gl.routines  as glroutines
from . import                  glvector_funcs


def init(self):
    """Calls :func:`compileShaders` and :func:`updateShaderState`.
    """

    self.shader = None

    compileShaders(self)
    updateShaderState(self)


def destroy(self):
    """Deletes the :class:`.GLSLShader`. """

    if self.shader is not None:
        self.shader.destroy()
    self.shader = None


def compileShaders(self):
    """Creates a :class:`.GLSLShader` for drawing this ``GLTensor``. This is
    done via a call to :func:`.gl21.glvector_funcs.compileShaders`.
    """
    self.shader = glvector_funcs.compileShaders(self, 'gltensor', indexed=True)


def updateShaderState(self):
    """Updates the state of the vertex and fragment shaders. The fragment
    shader is updated via the :func:`.gl21.glvector_funcs.updateShaderState`
    function.
    """

    if not self.ready():
        return

    image  = self.image
    shader = self.shader
    opts   = self.displayOpts

    shader.load()

    changed = glvector_funcs.updateShaderState(self)

    # Texture -> value value offsets/scales
    # used by the vertex and fragment shaders
    v1ValXform  = self.v1Texture.voxValXform
    v2ValXform  = self.v2Texture.voxValXform
    v3ValXform  = self.v3Texture.voxValXform
    l1ValXform  = self.l1Texture.voxValXform
    l2ValXform  = self.l2Texture.voxValXform
    l3ValXform  = self.l3Texture.voxValXform

    # Other miscellaneous uniforms
    imageShape    = image.shape[:3]
    resolution    = opts.tensorResolution
    tensorScale   = opts.tensorScale
    xFlip         = opts.orientFlip

    l1           = self.l1
    l1min, l1max = l1.dataRange
    eigValNorm   = 0.5 / max((abs(l1min), abs(l1max)))
    eigValNorm  *= tensorScale / 100.0

    # Define the light position in
    # the eye coordinate system
    lightPos  = np.array([-1, -1, 4], dtype=np.float32)
    lightPos /= np.sqrt(np.sum(lightPos ** 2))

    # Textures used by the vertex shader
    changed |= shader.set('v1Texture', 8)
    changed |= shader.set('v2Texture', 9)
    changed |= shader.set('v3Texture', 10)
    changed |= shader.set('l1Texture', 11)
    changed |= shader.set('l2Texture', 12)
    changed |= shader.set('l3Texture', 13)

    # Texture value -> actual
    # value transformations
    changed |= shader.set('v1ValXform', v1ValXform)
    changed |= shader.set('v2ValXform', v2ValXform)
    changed |= shader.set('v3ValXform', v3ValXform)
    changed |= shader.set('l1ValXform', l1ValXform)
    changed |= shader.set('l2ValXform', l2ValXform)
    changed |= shader.set('l3ValXform', l3ValXform)

    # Other settings
    changed |= shader.set('xFlip',      xFlip)
    changed |= shader.set('imageShape', imageShape)
    changed |= shader.set('eigValNorm', eigValNorm)
    changed |= shader.set('lighting',   opts.lighting)
    changed |= shader.set('lightPos',   lightPos)

    # Vertices of a unit sphere. The vertex
    # shader will transform these vertices
    # into the tensor ellipsoid for each
    # voxel.
    vertices, indices = glroutines.unitSphere(resolution)

    self.nVertices = len(indices)

    shader.setAtt('vertex', vertices)
    shader.setIndices(indices)
    shader.unload()

    return changed


def preDraw(self):
    """Must be called before :func:`draw`. Loads the shader programs, and
    does some shader state configuration.
    """

    shader = self.shader
    shader.load()

    # Calculate a transformation matrix for
    # normal vectors - T(I(MV matrix))

    # We transpose mvMat because OpenGL is column-major
    mvMat        = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)[:3, :3].T
    v2dMat       = self.displayOpts.getTransform('voxel', 'display')[:3, :3]

    normalMatrix = transform.concat(mvMat, v2dMat)
    normalMatrix = npla.inv(normalMatrix).T

    shader.set('normalMatrix', normalMatrix)

    gl.glEnable(gl.GL_CULL_FACE)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
    gl.glCullFace(gl.GL_BACK)


def draw(self, zpos, xform=None, bbox=None):
    """Generates voxel coordinates for each tensor to be drawn, does some
    final shader state configuration, and draws the tensors.
    """

    opts   = self.displayOpts
    shader = self.shader
    v2dMat = opts.getTransform('voxel',   'display')

    if xform is None: xform = v2dMat
    else:             xform = transform.concat(v2dMat, xform)

    voxels  = self.generateVoxelCoordinates(zpos, bbox)
    nVoxels = len(voxels)

    # Set divisor to 1, so we use one set of
    # voxel coordinates for every sphere drawn
    shader.setAtt('voxel',           voxels, divisor=1)
    shader.set(   'voxToDisplayMat', xform)
    shader.loadAtts()

    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, nVoxels)


def postDraw(self):
    """Unloads the shader program. """

    self.shader.unloadAtts()
    self.shader.unload()

    gl.glDisable(gl.GL_CULL_FACE)
    gl.glDisable(gl.GL_DEPTH_TEST)
