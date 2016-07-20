#!/usr/bin/env python
#
# glcsd_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools                    as it

import numpy                        as np
import numpy.linalg                 as npla

import OpenGL.GL                    as gl

import OpenGL.GL.ARB.draw_instanced as arbdi

import fsl.utils.transform          as transform
import fsleyes.gl.shaders           as shaders
import fsleyes.gl.textures          as textures
import fsleyes.gl.routines          as glroutines


def init(self):

    self.shader     = None
    self.radTexture = textures.Texture3D('blah')

    compileShaders(self)
    updateShaderState(self)


def destroy(self):
    if self.shader is not None:
        self.shader.destroy()
        self.shader = None
        
    if self.radTexture is not None:
        self.radTexture.destroy()
        self.radTexture = None 


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

    vertices, indices = glroutines.unitSphere(opts.csdResolution)

    self.vertices   = vertices
    self.indices    = indices
    self.nVertices  = len(indices)

    shader.set('radTexture',  0)

    shader.setAtt('vertex', self.vertices)
    shader.setIndices(indices)

    shader.unload()

def preDraw(self):
    shader = self.shader

    shader.load()

    # Calculate a transformation matrix for
    # normal vectors - T(I(MV matrix)) 
    mvMat        = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)[:3, :3]
    v2dMat       = self.displayOpts.getTransform('voxel', 'display')[:3, :3]
    
    normalMatrix = transform.concat(mvMat, v2dMat)
    normalMatrix = npla.inv(normalMatrix).T

    shader.set('normalMatrix', normalMatrix)

    self.radTexture.bindTexture(gl.GL_TEXTURE0)

    gl.glEnable(gl.GL_CULL_FACE)
    gl.glCullFace(gl.GL_BACK) 


def draw(self, zpos, xform=None):
    
    image  = self.image
    shape  = image.shape[:3]
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

    voxels = transform.transform(voxels, d2vMat)
    voxels = np.array(np.round(voxels), dtype=np.float32)

    print 'Calculating radii for {} voxels'.format(voxels.shape[0])
    radii  = self.getRadii(voxels)
    print 'Done'
    
    radTexShape = np.array(list(radii.shape) + [1, 1])

    # TODO This will break for
    #      odd-sized dimensions
    while np.any(radTexShape > 1024):
        imin = np.argmin(radTexShape)
        imax = np.argmax(radTexShape)

        # Find the lowest integer divisor
        # of the maximum dimension size
        divisor = 0
        for i in range(2, 10):
            if radTexShape[imax] % i == 0:
                divisor = i
                break

        radTexShape[imax] /= divisor
        radTexShape[imin] *= divisor

    print 'Reshaping radius: {} -> {}'.format(radii.shape, radTexShape)

    radii = radii.reshape(radTexShape, order='F')

    self.radTexture.set(data=radii)

    print 'Done'
    
    rt = self.radTexture.refreshThread()
    if rt is not None:
        rt.join()

    shader.setAtt('voxel', voxels, divisor=1)
    shader.set('voxToDisplayMat', xform)
    shader.set('radTexShape', radTexShape)

    shader.loadAtts()
    
    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, len(voxels))


def postDraw(self):
    self.shader.unloadAtts()
    self.shader.unload()
    self.radTexture.unbindTexture()
    
    gl.glDisable(gl.GL_CULL_FACE)
