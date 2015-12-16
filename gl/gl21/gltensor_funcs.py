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
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.instanced_arrays as arbia
import OpenGL.GL.ARB.draw_instanced   as arbdi

import fsl.utils.transform      as transform
import fsl.fsleyes.gl.resources as glresources
import fsl.fsleyes.gl.routines  as glroutines
import fsl.fsleyes.gl.textures  as textures
import fsl.fsleyes.gl.shaders   as shaders


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

    self.vertexBuffer = gl.glGenBuffers(1)
    self.indexBuffer  = gl.glGenBuffers(1)
    self.voxelBuffer  = gl.glGenBuffers(1)

    self.shaders = None

    compileShaders(self)
    updateShaderState(self)


def destroy(self):
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.indexBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.voxelBuffer))
    gl.glDeleteProgram(self.shaders)
    
    names = ['v1', 'v2', 'v3', 'l1', 'l2', 'l3']

    for name in names:
        attrName = '{}Texture'.format(name)
        tex      = getattr(self, attrName)
        
        glresources.delete(tex.getTextureName())
        setattr(self, attrName, None)


def compileShaders(self):
    
    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    vertAtts     = ['voxel', 'vertex']
 
    vertUniforms = ['v1Texture',       'v2Texture',  'v3Texture',
                    'l1Texture',       'l2Texture',  'l3Texture',
                    'v1ValXform',      'v2ValXform', 'v3ValXform',
                    'l1ValXform',      'l2ValXform', 'l3ValXform',
                    'voxToDisplayMat', 'imageShape', 'resolution',
                    'lighting',        'lightPos',   'normalMatrix',
                    'eigValNorm',      'zax']

    fragUniforms = ['imageTexture',   'modulateTexture', 'clipTexture',
                    'clipThreshold',  'xColourTexture',  'yColourTexture',
                    'zColourTexture', 'voxValXform',     'cmapXform',
                    'imageShape',     'useSpline']


    self.shaderVars = shaders.getShaderVars(self.shaders,
                                            vertAtts,
                                            vertUniforms,
                                            fragUniforms)


def updateShaderState(self):

    gl.glUseProgram(self.shaders)

    opts  = self.displayOpts
    svars = self.shaderVars

    # Textures used by the fragment shader
    gl.glUniform1i(svars['imageTexture'],    0)
    gl.glUniform1i(svars['modulateTexture'], 1)
    gl.glUniform1i(svars['clipTexture'],     2)
    gl.glUniform1i(svars['xColourTexture'],  3)
    gl.glUniform1i(svars['yColourTexture'],  4)
    gl.glUniform1i(svars['zColourTexture'],  5)

    # Textures used by the vertex shader
    gl.glUniform1i(svars['v1Texture'], 6)
    gl.glUniform1i(svars['v2Texture'], 7)
    gl.glUniform1i(svars['v3Texture'], 8)
    gl.glUniform1i(svars['l1Texture'], 9)
    gl.glUniform1i(svars['l2Texture'], 10)
    gl.glUniform1i(svars['l3Texture'], 11)

    # Texture -> value value offsets/scales
    # used by the vertex and fragment shaders
    cmapXform   = self.xColourTexture.getCoordinateTransform()
    voxValXform = self.imageTexture.voxValXform
    v1ValXform  = self.v1Texture.voxValXform
    v2ValXform  = self.v2Texture.voxValXform
    v3ValXform  = self.v3Texture.voxValXform
    l1ValXform  = self.l1Texture.voxValXform
    l2ValXform  = self.l2Texture.voxValXform
    l3ValXform  = self.l3Texture.voxValXform
    
    voxValXform = np.array(voxValXform, dtype=np.float32).ravel('C')
    cmapXform   = np.array(cmapXform,   dtype=np.float32).ravel('C')
    v1ValXform  = np.array(v1ValXform,  dtype=np.float32).ravel('C')
    v2ValXform  = np.array(v2ValXform,  dtype=np.float32).ravel('C')
    v3ValXform  = np.array(v3ValXform,  dtype=np.float32).ravel('C')
    l1ValXform  = np.array(l1ValXform,  dtype=np.float32).ravel('C')
    l2ValXform  = np.array(l2ValXform,  dtype=np.float32).ravel('C')
    l3ValXform  = np.array(l3ValXform,  dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(svars['voxValXform'], 1, False, voxValXform)
    gl.glUniformMatrix4fv(svars['cmapXform'],   1, False, cmapXform)
    gl.glUniformMatrix4fv(svars['v1ValXform'],  1, False, v1ValXform)
    gl.glUniformMatrix4fv(svars['v2ValXform'],  1, False, v2ValXform)
    gl.glUniformMatrix4fv(svars['v3ValXform'],  1, False, v3ValXform)
    gl.glUniformMatrix4fv(svars['l1ValXform'],  1, False, l1ValXform)
    gl.glUniformMatrix4fv(svars['l2ValXform'],  1, False, l2ValXform)
    gl.glUniformMatrix4fv(svars['l3ValXform'],  1, False, l3ValXform)

    # Other miscellaneous uniforms
    imageShape    = np.array(self.image.shape[:3], dtype=np.float32)
    resolution    = opts.tensorResolution
    clipThreshold = opts.clipThreshold
    tensorScale   = opts.tensorScale
    lighting      = 1 if opts.lighting else 0
    useSpline     = 0

    l1          = self.image.L1()
    eigValNorm  = 0.5 / abs(l1.data).max()
    eigValNorm *= tensorScale / 100.0

    invClipValXform = self.clipTexture .invVoxValXform
    clipThreshold   = clipThreshold * invClipValXform[0, 0] + \
                                      invClipValXform[3, 0] 

    gl.glUniform3fv(svars['imageShape'], 1,  imageShape)
    gl.glUniform1f( svars['resolution'],     resolution)
    gl.glUniform1f( svars['eigValNorm'],     eigValNorm)
    gl.glUniform1f( svars['lighting'],       lighting)
    gl.glUniform1f( svars['clipThreshold'],  clipThreshold)
    gl.glUniform1f( svars['useSpline'],      useSpline)
    
    # Vertices of a unit sphere. The vertex
    # shader will transform these vertices
    # into the tensor ellipsoid for each
    # voxel.
    vertices, indices = glroutines.unitSphere(resolution)
    
    self.nVertices = len(indices)
    vertices       = vertices.ravel('C')

    gl.glUseProgram(0)    

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)
    gl.glBufferData(
        gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)


def preDraw(self):
    """Must be called before :func:`draw`. Loads the shader programs, binds
    textures, and enables vertex arrays.
    """
    gl.glUseProgram(self.shaders)

    svars = self.shaderVars

    # Define the light position in
    # the world coordinate system
    lightPos = np.array([1, 1, -1], dtype=np.float32)

    lightPos[self.zax] *= 3

    # Transform the light position into
    # the display coordinate system,
    # and normalise to unit length
    mvMat     = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)[:3, :3]
    lightPos  = np.dot(mvMat, lightPos)
    lightPos /= np.sqrt(np.sum(lightPos ** 2))

    # Calculate a transformation matrix for
    # normal vectors - T(I(MV matrix))
    normalMatrix = npla.inv(mvMat).T

    gl.glUniform1f(       svars['zax'],                    self.zax)
    gl.glUniform3fv(      svars['lightPos'],     1,        lightPos)
    gl.glUniformMatrix3fv(svars['normalMatrix'], 1, False, normalMatrix) 
    
    self.v1Texture.bindTexture(gl.GL_TEXTURE6)
    self.v2Texture.bindTexture(gl.GL_TEXTURE7)
    self.v3Texture.bindTexture(gl.GL_TEXTURE8)
    self.l1Texture.bindTexture(gl.GL_TEXTURE9)
    self.l2Texture.bindTexture(gl.GL_TEXTURE10)
    self.l3Texture.bindTexture(gl.GL_TEXTURE11)
    
    gl.glEnableVertexAttribArray(svars['voxel'])
    gl.glEnableVertexAttribArray(svars['vertex'])

    gl.glEnable(gl.GL_CULL_FACE)
    gl.glCullFace(gl.GL_BACK)
    

def draw(self, zpos, xform=None):

    image  = self.image
    opts   = self.displayOpts
    svars  = self.shaderVars
    v2dMat = opts.getTransform('voxel',   'display')
    d2vMat = opts.getTransform('display', 'voxel')

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
    
    voxels  = np.array(voxels, dtype=np.float32).ravel('C')

    # Copy the voxel coordinates to the voxel buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.voxelBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, voxels.nbytes, voxels, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        svars['voxel'], 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    # Use one set of voxel coordinates for every sphere drawn
    arbia.glVertexAttribDivisorARB(svars['voxel'], 1)

    # Bind the vertex buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glVertexAttribPointer(
        svars['vertex'], 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    if xform is None: xform = v2dMat
    else:             xform = transform.concat(v2dMat, xform)
    
    xform = np.array(xform, dtype=np.float32).ravel('C') 
    gl.glUniformMatrix4fv(svars['voxToDisplayMat'], 1, False, xform)

    # And the vertex index buffer
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)

    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, nVoxels)


def postDraw(self):
    
    svars = self.shaderVars
    
    gl.glUseProgram(0)

    gl.glDisable(gl.GL_CULL_FACE)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
    
    self.v1Texture.unbindTexture()
    self.v2Texture.unbindTexture()
    self.v3Texture.unbindTexture()
    self.l1Texture.unbindTexture()
    self.l2Texture.unbindTexture()
    self.l3Texture.unbindTexture()
    
    gl.glDisableVertexAttribArray(svars['voxel'])
    gl.glDisableVertexAttribArray(svars['vertex'])
