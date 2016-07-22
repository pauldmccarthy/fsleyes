#!/usr/bin/env python
#
# glcsd_funcs.py - Functions used by GLCSD instances.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions which are used by :class:`.GLCSD` instances
for rendering :class:`.Image` overlays which contain spherical deconvolution
diffusion model fits, in an OpenGL 2.1 compatible manner..

The functions defined in this module are intended to be called by
:class:`.GLCSD` instances.

For each voxel, a sphere is drawn, with the position of each vertex on the
sphere adjusted by the SD coefficients (radii). For one draw call, the radii
for all voxels and vertices is calculated, and stored in a texture. These
radii values are then accessed by the ``glcsd_vert.glsl`` vertex shader.
"""


import numpy                        as np
import numpy.linalg                 as npla

import OpenGL.GL                    as gl

import OpenGL.GL.ARB.draw_instanced as arbdi

import fsl.utils.transform          as transform
import fsleyes.gl.shaders           as shaders
import fsleyes.gl.routines          as glroutines


def init(self):
    """Called by :meth:`.GLCSD.__init__`. Calls :func:`compileShaders` and
    :func:`updateShaderState`.
    """

    self.shader = None
    compileShaders(self)
    updateShaderState(self)


def destroy(self):
    """Destroys the shader program """
    
    if self.shader is not None:
        self.shader.destroy()
        self.shader = None
        

def compileShaders(self):
    """Creates a :class:`.GLSLShader`, and attaches it to this :class:`.GLCSD`
    instance as an attribute called ``shader``.
    """
    
    if self.shader is not None:
        self.shader.destroy() 

    vertSrc = shaders.getVertexShader(  'glcsd')
    fragSrc = shaders.getFragmentShader('glcsd')
    
    self.shader = shaders.GLSLShader(vertSrc, fragSrc, indexed=True)


def updateShaderState(self):
    """Updates the state of the vertex and fragment shaders. """
    
    shader = self.shader
    image  = self.image
    opts   = self.displayOpts

    lightPos  = np.array([-1, -1, 4], dtype=np.float32)
    lightPos /= np.sqrt(np.sum(lightPos ** 2))

    shape = image.shape[:3]
    xFlip = opts.neuroFlip and image.isNeurological()

    shader.load()

    changed  = False
    changed |= shader.set('xFlip',       xFlip)
    changed |= shader.set('imageShape',  shape)
    changed |= shader.set('lighting',    opts.lighting)
    changed |= shader.set('lightPos',    lightPos)
    changed |= shader.set('nVertices',   opts.csdResolution ** 2)
    changed |= shader.set('sizeScaling', opts.size / 100.0)
    changed |= shader.set('radTexture',  0)
    changed |= shader.set('cmapTexture',  1)

    # Vertices only need to be re-generated
    # if the csdResolution has changed.
    if changed:
        vertices, indices = glroutines.unitSphere(opts.csdResolution)

        self.vertices  = vertices
        self.indices   = indices
        self.nVertices = len(indices)

        shader.setAtt('vertex', self.vertices)
        shader.setIndices(indices)

    shader.unload()

    return changed


def preDraw(self):
    """Called by :meth:`.GLCSD.preDraw`. Loads the shader program, and updates
    some shader attributes.
    """
    shader = self.shader

    shader.load()

    # Calculate a transformation matrix for
    # normal vectors - T(I(MV matrix)) 
    mvMat        = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)[:3, :3]
    v2dMat       = self.displayOpts.getTransform('voxel', 'display')[:3, :3]
    
    normalMatrix = transform.concat(mvMat, v2dMat)
    normalMatrix = npla.inv(normalMatrix).T

    shader.set('normalMatrix', normalMatrix)

    gl.glEnable(gl.GL_CULL_FACE)
    gl.glCullFace(gl.GL_BACK) 


def draw(self, zpos, xform=None, bbox=None):
    """Called by :meth:`.GLCSD.draw`. Draws the scene. """

    opts   = self.displayOpts
    shader = self.shader
    v2dMat = opts.getTransform('voxel',   'display')

    if xform is None: xform = v2dMat
    else:             xform = transform.concat(v2dMat, xform)

    voxels      = self.generateVoxelCoordinates(zpos, bbox)
    radTexShape = self.updateRadTexture(voxels)

    shader.setAtt('voxel',           voxels, divisor=1)
    shader.set(   'voxToDisplayMat', xform)
    shader.set(   'radTexShape',     radTexShape)

    shader.loadAtts()
    
    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, len(voxels))


def postDraw(self):
    """Called by :meth:`.GLCSD.draw`. Cleans up the shader program and GL
    state.
    """
    
    self.shader.unloadAtts()
    self.shader.unload()
    gl.glDisable(gl.GL_CULL_FACE)
