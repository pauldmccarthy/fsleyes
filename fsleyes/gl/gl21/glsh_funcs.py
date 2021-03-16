#!/usr/bin/env python
#
# glsh_funcs.py - Functions used by GLSH instances.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions which are used by :class:`.GLSH` instances
for rendering :class:`.Image` overlays which contain fibre orientation
distribution (FOD) spherical harmonic (SH) coefficients, in an OpenGL 2.1
compatible manner.  The functions defined in this module are intended to be
called by :class:`.GLSH` instances.


For each voxel, a sphere is drawn, with the position of each vertex on the
sphere adjusted by the SH coefficients (radii). For one draw call, the radii
for all voxels and vertices is calculated, and stored in a texture.


Different vertex/fragment shaders are used depending upon the current settings
of the :class:`.SHOpts` instance associated with the :class:`.GLSH`. If the
:attr:`.VectorOpts.colourImage` property is set, the ``glsh_volume_vert.glsl``
andf ``glvolume_frag.glsl`` shaders are used. In this case, the FODs are each
voxel are coloured according to the values in the ``colourImage``.  Otherwise,
the ``glsh_vert.glsl`` and ``glsh_frag.glsl`` shaders are used. In this case,
the vertices of each FOD are coloured according to their orientation, or to
their radius.
"""


import numpy                        as np
import numpy.linalg                 as npla

import OpenGL.GL                    as gl

import OpenGL.GL.ARB.draw_instanced as arbdi

import fsl.transform.affine         as affine
import fsleyes.gl.shaders           as shaders


def destroy(self):
    """Destroys the shader program """

    if self.shader is not None:
        self.shader.destroy()
        self.shader = None


def compileShaders(self):
    """Creates a :class:`.GLSLShader`, and attaches it to this :class:`.GLSH`
    instance as an attribute called ``shader``.
    """

    if self.shader is not None:
        self.shader.destroy()

    opts                     = self.opts
    self.useVolumeFragShader = opts.colourImage is not None

    if self.useVolumeFragShader:
        vertShader = 'glsh_volume'
        fragShader = 'glvolume'
    else:
        vertShader = 'glsh'
        fragShader = 'glsh'

    vertSrc = shaders.getVertexShader(  vertShader)
    fragSrc = shaders.getFragmentShader(fragShader)

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, indexed=True)


def updateShaderState(self):
    """Updates the state of the vertex and fragment shaders. """

    shader  = self.shader
    image   = self.image
    opts    = self.opts

    if shader is None:
        return

    lightPos  = np.array([-1, -1, 4], dtype=np.float32)
    lightPos /= np.sqrt(np.sum(lightPos ** 2))

    shape = image.shape[:3]
    xFlip = opts.orientFlip

    if   opts.colourMode == 'direction': colourMode = 0
    elif opts.colourMode == 'radius':    colourMode = 1

    modLow,  modHigh  = self.getModulateRange()
    clipLow, clipHigh = self.getClippingRange()
    modMode           = {'brightness' : 0,
                         'alpha'      : 1}[opts.modulateMode]

    clipXform   = self.getAuxTextureXform('clip')
    colourXform = self.getAuxTextureXform('colour')
    modXform    = self.getAuxTextureXform('modulate')

    shader.load()

    changed  = False
    changed |= shader.set('xFlip',       xFlip)
    changed |= shader.set('imageShape',  shape)
    changed |= shader.set('lighting',    opts.lighting)
    changed |= shader.set('lightPos',    lightPos)
    changed |= shader.set('nVertices',   self.vertices.shape[0])
    changed |= shader.set('sizeScaling', opts.size / 100.0)
    changed |= shader.set('radTexture',  4)

    if self.useVolumeFragShader:

        voxValXform     = self.colourTexture.voxValXform
        invVoxValXform  = self.colourTexture.invVoxValXform
        texZero         = 0.0 * invVoxValXform[0, 0] + invVoxValXform[0, 3]
        img2CmapXform   = affine.concat(
            self.cmapTexture.getCoordinateTransform(),
            voxValXform)

        changed |= shader.set('clipTexture',      1)
        changed |= shader.set('imageTexture',     2)
        changed |= shader.set('colourTexture',    3)
        changed |= shader.set('negColourTexture', 3)
        changed |= shader.set('img2CmapXform',    img2CmapXform)
        changed |= shader.set('imageIsClip',      False)
        changed |= shader.set('useNegCmap',       False)
        changed |= shader.set('useSpline',        False)
        changed |= shader.set('clipLow',          clipLow)
        changed |= shader.set('clipHigh',         clipHigh)
        changed |= shader.set('texZero',          texZero)
        changed |= shader.set('invertClip',       False)
        changed |= shader.set('colourCoordXform', colourXform)
        changed |= shader.set('clipCoordXform',   clipXform)

    else:

        cmapXform            = self.cmapTexture.getCoordinateTransform()
        colours, colourXform = self.getVectorColours()

        changed |= shader.set('modulateTexture',  0)
        changed |= shader.set('clipTexture',      1)
        changed |= shader.set('cmapTexture',      3)
        changed |= shader.set('clipLow',          clipLow)
        changed |= shader.set('clipHigh',         clipHigh)
        changed |= shader.set('modLow',           modLow)
        changed |= shader.set('modHigh',          modHigh)
        changed |= shader.set('modulateMode',     modMode)
        changed |= shader.set('colourMode',       colourMode)
        changed |= shader.set('xColour',          colours[0])
        changed |= shader.set('yColour',          colours[1])
        changed |= shader.set('zColour',          colours[2])
        changed |= shader.set('colourXform',      colourXform)
        changed |= shader.set('cmapXform',        cmapXform)
        changed |= shader.set('clipCoordXform',   clipXform)
        changed |= shader.set('modCoordXform',    modXform)

    shader.setAtt('vertex',   self.vertices)
    shader.setAtt('vertexID', self.vertIdxs)
    shader.setIndices(        self.indices)

    shader.unload()

    return changed


def preDraw(self, xform=None, bbox=None):
    """Called by :meth:`.GLSH.preDraw`. Loads the shader program, and updates
    some shader attributes.
    """
    shader = self.shader

    shader.load()

    # Calculate a transformation matrix for
    # normal vectors - T(I(MV matrix))
    # We transpose mvMat because OpenGL is column-major
    mvMat        = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)[:3, :3].T
    v2dMat       = self.opts.getTransform('voxel', 'display')[:3, :3]

    normalMatrix = affine.concat(mvMat, v2dMat)
    normalMatrix = npla.inv(normalMatrix).T

    shader.set('normalMatrix', normalMatrix)

    gl.glEnable(gl.GL_CULL_FACE)
    gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glCullFace(gl.GL_BACK)


def draw2D(self, zpos, axes, xform=None, bbox=None):
    """Called by :meth:`.GLSH.draw2D`. Draws the scene. """

    opts   = self.opts
    shader = self.shader
    v2dMat = opts.getTransform('voxel',   'display')

    if xform is None: xform = v2dMat
    else:             xform = affine.concat(v2dMat, xform)

    voxels              = self.generateVoxelCoordinates2D(zpos, axes, bbox)
    voxels, radTexShape = self.updateRadTexture(voxels)

    if len(voxels) == 0:
        return

    voxIdxs = np.arange(voxels.shape[0], dtype=np.float32)

    shader.setAtt('voxel',           voxels,  divisor=1)
    shader.setAtt('voxelID',         voxIdxs, divisor=1)
    shader.set(   'voxToDisplayMat', xform)
    shader.set(   'radTexShape',     radTexShape)
    shader.set(   'radXform',        self.radTexture.voxValXform)

    shader.loadAtts()

    arbdi.glDrawElementsInstancedARB(
        gl.GL_TRIANGLES, self.nVertices, gl.GL_UNSIGNED_INT, None, len(voxels))


def draw3D(self, xform=None, bbox=None):
    pass


def postDraw(self, xform=None, bbox=None):
    """Called by :meth:`.GLSH.draw`. Cleans up the shader program and GL
    state.
    """

    self.shader.unloadAtts()
    self.shader.unload()
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glDisable(gl.GL_DEPTH_TEST)
