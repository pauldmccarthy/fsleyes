#!/usr/bin/env python
#
# glcsd_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools                    as it

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

    shape = image.shape[:3]
    xFlip = opts.neuroFlip and image.isNeurological()

    shader.load()

    changed  = False
    changed |= shader.set('xFlip',      xFlip)
    changed |= shader.set('imageShape', shape)
    changed |= shader.set('lighting',   opts.lighting)

    allVertices = getattr(type(self), 'allSpheres', None)

    if allVertices is None:

        sphere, idxs = glroutines.unitSphere(self.resolution)

        nverts    = sphere.shape[0]
        nvoxels   = np.prod(shape)

        print 'Preparing vertices for {} voxels'.format(nvoxels)
        
        allVoxels = np.mgrid[:shape[0], :shape[1], :shape[2]]
        allVoxels = allVoxels.T.reshape(nvoxels, 3)
        allVoxels = np.array(allVoxels, dtype=np.uint32)

        print 'allvoxels', allVoxels.dtype, allVoxels.shape
        print allVoxels

        allSpheres = np.tile(sphere, (nvoxels, 1))
        
        for i, (z, y, x) in enumerate(it.product(range(shape[2]),
                                                 range(shape[1]),
                                                 range(shape[0]))):

            si = i  * nverts
            ei = si + nverts

            radii   = np.dot(self.shCoefs, image[x, y, z, :])
            allSpheres[si:ei, :] *= np.tile(radii.reshape((-1, 1)), (1, 3))
        
        allVoxels = np.repeat(allVoxels, nverts, 0)
        
        allIdxs    = np.tile(idxs,    nvoxels)
        allIdxs   += np.repeat(np.arange(0, nvoxels * nverts, nverts, dtype=np.uint32),
                               len(idxs))

        print 'nVertsPerVoxel', len(idxs)
        print 'allSpheres', allSpheres.dtype, allSpheres.shape
        print allSpheres
        print 'allIdxs', allIdxs.dtype, allIdxs.shape
        print allIdxs
        print 'allvoxels', allVoxels.dtype, allVoxels.shape
        print allVoxels

        type(self).allSpheres     = allSpheres
        type(self).allVoxels      = allVoxels
        type(self).allIdxs        = allIdxs
        type(self).nVertsPerVoxel = len(idxs)
         
        print 'Done'

    self.nVertsPerVoxel = type(self).nVertsPerVoxel
    self.allIdxs        = type(self).allIdxs
    self.allVoxels      = type(self).allVoxels
    self.allSpheres     = type(self).allSpheres

    shader.setAtt('vertex', self.allSpheres)
    shader.setAtt('voxel',  self.allVoxels)
    
    shader.unload()


def preDraw(self):
    shader = self.shader

    shader.load()

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

    voxels  = transform.transform(voxels, d2vMat)
    nvoxels = len(voxels)

    voxelOffsets = np.array(voxels[:, 0]            + \
                            voxels[:, 1] * shape[0] + \
                            voxels[:, 2] * shape[0] * shape[1],
                            dtype=np.uint32) * self.nVertsPerVoxel

    voxelOffsets  = np.repeat(voxelOffsets, self.nVertsPerVoxel)

    off = np.tile(np.arange(self.nVertsPerVoxel, dtype=np.uint32), nvoxels)

    voxelOffsets += off

    indices = self.allIdxs[voxelOffsets]

    shader.set('voxToDisplayMat', xform)
    
    shader.setIndices(indices)

    shader.loadAtts()
    
    gl.glDrawElements(gl.GL_QUADS, len(indices), gl.GL_UNSIGNED_INT, None)


def postDraw(self):
    self.shader.unloadAtts()
    self.shader.unload()
    gl.glDisable(gl.GL_CULL_FACE)
