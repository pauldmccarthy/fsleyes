#!/usr/bin/env python
#
# gltensor_funcs.py - OpenGL2.1 functions used by the GLTensor class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import numpy                          as np
import numpy.linalg                   as npla
import OpenGL.GL                      as gl
import OpenGL.GL.ARB.draw_instanced   as arbdi

import fsl.utils.transform      as transform
import fsl.fsleyes.gl.resources as glresources
import fsl.fsleyes.gl.routines  as glroutines
import fsl.fsleyes.gl.textures  as textures
import                             glvector_funcs


log = logging.getLogger(__name__)


def init(self):
    """Compiles and configures the vertex and fragment shader programs, and
    creates textures and vertex buffers.
    """

    image = self.image

    v1 = image.V1()
    v2 = image.V2()
    v3 = image.V3()
    l1 = image.L1()
    l2 = image.L2()
    l3 = image.L3()


    def vPrefilter(d):
        return d.transpose((3, 0, 1, 2))

    names = ['v1', 'v2', 'v3', 'l1', 'l2', 'l3']
    imgs  = [ v1,   v2,   v3,   l1,   l2,   l3]

    for  name, img in zip(names, imgs):
        texName = '{}_{}_{}'.format(type(self).__name__, name, id(img))

        if name[0] == 'v':
            prefilter = vPrefilter
            nvals     = 3
        else:
            prefilter = None
            nvals     = 1
        
        tex = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            img,
            nvals=nvals,
            normalise=True,
            prefilter=prefilter)

        setattr(self, '{}Texture'.format(name), tex)

    self.shader = None

    compileShaders(self)
    updateShaderState(self)


def destroy(self):
    self.shader.delete()
    self.shader = None
    
    names = ['v1', 'v2', 'v3', 'l1', 'l2', 'l3']

    for name in names:
        attrName = '{}Texture'.format(name)
        tex      = getattr(self, attrName)
        
        glresources.delete(tex.getTextureName())
        setattr(self, attrName, None)


def compileShaders(self):
    self.shader = glvector_funcs.compileShaders(self, indexed=True)


def updateShaderState(self):

    shader = self.shader
    opts   = self.displayOpts
    
    shader.load()
    glvector_funcs.updateFragmentShaderState(self)

    # Texture -> value value offsets/scales
    # used by the vertex and fragment shaders
    v1ValXform  = self.v1Texture.voxValXform
    v2ValXform  = self.v2Texture.voxValXform
    v3ValXform  = self.v3Texture.voxValXform
    l1ValXform  = self.l1Texture.voxValXform
    l2ValXform  = self.l2Texture.voxValXform
    l3ValXform  = self.l3Texture.voxValXform

    # Other miscellaneous uniforms
    imageShape    = self.image.shape[:3]
    resolution    = opts.tensorResolution
    tensorScale   = opts.tensorScale

    l1          = self.image.L1()
    eigValNorm  = 0.5 / np.abs(l1.data).max()
    eigValNorm *= tensorScale / 100.0

    # Define the light position in
    # the eye coordinate system
    lightPos  = np.array([-1, -1, 4], dtype=np.float32)
    lightPos /= np.sqrt(np.sum(lightPos ** 2)) 
 
    # Textures used by the vertex shader
    shader.set('v1Texture', 8)
    shader.set('v2Texture', 9)
    shader.set('v3Texture', 10)
    shader.set('l1Texture', 11)
    shader.set('l2Texture', 12)
    shader.set('l3Texture', 13)
    
    shader.set('v1ValXform', v1ValXform)
    shader.set('v2ValXform', v2ValXform)
    shader.set('v3ValXform', v3ValXform)
    shader.set('l1ValXform', l1ValXform)
    shader.set('l2ValXform', l2ValXform)
    shader.set('l3ValXform', l3ValXform)

    shader.set('imageShape', imageShape)
    shader.set('eigValNorm', eigValNorm)
    shader.set('lighting',   opts.lighting)
    shader.set('lightPos',   lightPos)
    
    # Vertices of a unit sphere. The vertex
    # shader will transform these vertices
    # into the tensor ellipsoid for each
    # voxel.
    vertices, indices = glroutines.unitSphere(resolution)
    
    self.nVertices = len(indices)

    shader.setAtt('vertex', vertices)
    shader.setIndices(indices)
    shader.unload()


def preDraw(self):
    """Must be called before :func:`draw`. Loads the shader programs, binds
    textures, and enables vertex arrays.
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

    self.v1Texture.bindTexture(gl.GL_TEXTURE8)
    self.v2Texture.bindTexture(gl.GL_TEXTURE9)
    self.v3Texture.bindTexture(gl.GL_TEXTURE10)
    self.l1Texture.bindTexture(gl.GL_TEXTURE11)
    self.l2Texture.bindTexture(gl.GL_TEXTURE12)
    self.l3Texture.bindTexture(gl.GL_TEXTURE13)

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
        resolution = map(lambda r, p: max(r, p), resolution, image.pixdim[:3])

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
    shader.loadAtts()
    shader.setAtt('voxel',           voxels, divisor=1)
    shader.set(   'voxToDisplayMat', xform)

    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, nVoxels)


def postDraw(self):

    self.shader.unloadAtts()
    self.shader.unload()

    gl.glDisable(gl.GL_CULL_FACE)
    
    self.v1Texture.unbindTexture()
    self.v2Texture.unbindTexture()
    self.v3Texture.unbindTexture()
    self.l1Texture.unbindTexture()
    self.l2Texture.unbindTexture()
    self.l3Texture.unbindTexture()
