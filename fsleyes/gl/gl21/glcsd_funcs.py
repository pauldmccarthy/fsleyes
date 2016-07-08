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
    self.radTexture = None

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
    changed |= shader.set('xFlip',      xFlip)
    changed |= shader.set('imageShape', shape)
    changed |= shader.set('lighting',   opts.lighting)
    changed |= shader.set('resolution', self.resolution ** 2)

    vertices, indices = glroutines.unitSphere(self.resolution)

    self.radTexture, rts = configRadiusTexture(self)
    self.vertices   = vertices
    self.indices    = indices
    self.nVertices  = len(indices)

    print 'Vertices ({} / {})'.format(vertices.dtype, vertices.shape)
    # print vertices
    print 'Indices ({} / {})'.format(indices.dtype, indices.shape)
    # print indices
    
    shader.set('radTexture',  0)

    print 'Texture shape: {}'.format(rts)
    shader.set('radTexShape', rts)

    shader.setAtt('vertex', self.vertices)
    shader.setIndices(indices)

    shader.unload()


def configRadiusTexture(self):

    image   = self.image
    shape   = self.image.shape[:3]
    nverts  = self.resolution ** 2
    nvoxels = np.prod(shape)

    radTexShape = list(shape) + [nverts]
    radTexShape = np.array(radTexShape)

    print 'Figuring out radius texture shape '\
          '(starting with {})'.format(radTexShape)

    rprod = np.prod(radTexShape)

    while radTexShape[-1] != 1:
        imin          = np.argmin(radTexShape[:3])
        radTexShape[imin] *= 2
        radTexShape[-1]   /= 2

    radTexShape = radTexShape[:-1]

    print 'Got shape {} ({} == {})'.format(
        radTexShape,
        np.prod(radTexShape),
        rprod)

    print 'Calculating radii...',
        
    radii = np.zeros(nvoxels * nverts, dtype=np.uint8)

    for i, (z, y, x) in enumerate(it.product(range(shape[2]),
                                             range(shape[1]),
                                             range(shape[0]))):

        si           = i  * nverts
        ei           = si + nverts
        radii[si:ei] = 128 + np.dot(self.shCoefs, image[x, y, z, :]) * 127

        # radii[si:ei] = 95 + 128 * float(x) / (shape[0] - 1)
        # radii[i] = 95 + 128 * float(x) / (shape[0] - 1)

    radii = radii.reshape(radTexShape, order='F')

    print 'Finished'
        
    print 'Creating radius texture ...',

    tex = textures.Texture3D('blah', data=radii)

    rt = tex.refreshThread()
    if rt is not None:
        rt.join()

    print 'Finished'

    return tex, radTexShape


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

    shader.setAtt('voxel', voxels, divisor=1)
    shader.set('voxToDisplayMat', xform)

    shader.loadAtts()
    
    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, len(voxels)) 


def postDraw(self):
    self.shader.unloadAtts()
    self.shader.unload()
    self.radTexture.unbindTexture()
    
    gl.glDisable(gl.GL_CULL_FACE)
