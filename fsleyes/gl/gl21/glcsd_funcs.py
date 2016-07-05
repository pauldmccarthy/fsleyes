#!/usr/bin/env python
#
# glcsd_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                        as np

import OpenGL.GL                    as gl

import OpenGL.GL.ARB.draw_instanced as arbdi

import fsl.utils.transform          as transform
import fsleyes.gl.shaders           as shaders
import fsleyes.gl.routines          as glroutines


def init(self):

    self.shader = None

    compileShaders(self)
    updateShaderState(self)


def destroy(self):
    self.shader.destroy()
    self.shader = None


def compileShaders(self):
    
    if self.shader is not None:
        self.shader.destroy() 

    vertSrc = shaders.getVertexShader(  'glcsd')
    fragSrc = shaders.getFragmentShader('glcsd')
    
    self.shader = shaders.GLSLShader(vertSrc, fragSrc, indexed=True)


def updateShaderState(self):
    
    shader = self.shader
    image  = self.image
    opts   = self.displayOpts

    lightPos  = np.array([-1, -1, 4], dtype=np.float32)
    lightPos /= np.sqrt(np.sum(lightPos ** 2))

    imageShape = image.shape[:3]
    xFlip      = opts.neuroFlip and image.isNeurological()

    shader.load()

    changed  = False
    changed |= shader.set('xFlip',      xFlip)
    changed |= shader.set('imageShape', imageShape)
    changed |= shader.set('lighting',   opts.lighting)

    sphere, idxs   = glroutines.unitSphere(16)
    self.vertices  = sphere
    self.indices   = idxs
    self.nVertices = len(idxs)
    
    shader.setAtt('vertex', self.vertices)
    shader.setIndices(self.indices)

    shader.unload()


def preDraw(self):
    shader = self.shader

    shader.load()

    gl.glEnable(gl.GL_CULL_FACE)
    gl.glCullFace(gl.GL_BACK) 


def draw(self, zpos, xform=None):
    
    image  = self.image
    opts   = self.displayOpts
    shader = self.shader
    v2dMat = opts.getTransform('voxel',   'display')
    d2vMat = opts.getTransform('display', 'voxel')

    if xform is None: xform = v2dMat
    else:             xform = transform.concat(v2dMat, xform)

    resolution = np.array([opts.resolution] * 3)

    if opts.transform == 'id':
        resolution = resolution / min(image.pixdim[:3])
    elif opts.transform == 'pixdim':
        resolution = [max(r, p) for r, p in zip(resolution, image.pixdim[:3])]

    voxels = glroutines.calculateSamplePoints(
        image.shape,
        resolution,
        v2dMat,
        self.xax,
        self.yax)[0]

    voxels[:, self.zax] = zpos

    voxels  = transform.transform(voxels, d2vMat)
    nVoxels = len(voxels)

    # Set divisor to 1, so we use one set of
    # voxel coordinates for every sphere drawn
    shader.setAtt('voxel',           voxels, divisor=1)
    shader.set(   'voxToDisplayMat', xform)
    shader.loadAtts()
    
    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, nVoxels)


def postDraw(self):
    self.shader.unloadAtts()
    self.shader.unload()
    gl.glDisable(gl.GL_CULL_FACE)
