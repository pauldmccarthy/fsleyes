#!/usr/bin/env python
#
# gltensor_funcs.py - OpenGL2.1 functions used by the GLTensor class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLTensor`
class for rendering :class:`.TensorImage` overlays in an OpenGL 2.1 compatible
manner.


The eigenvalues and eigenvectors of the ``TensorImage`` are stored as 3D
:class:`.ImageTexture` instances, using the :mod:`.gl.resources` module. For
each voxel, the vertices of a unit sphere are passed to the ``gltensor``
vertex shader, which looks up the eigenvectors and values for the voxel, and
transforms the sphere accordingly.


The rendering code makes use of the OpenGL ``ARB_draw_instanced`` extension
so that voxel coordinates do not need to be repeated for every vertex of
a single tensor.


If the :attr:`.VectorOpts.colourImage` property is not set, the ``glvector``
fragment shader is used to colour the tensors. Otherwise, the ``glvolume``
fragment shader is used to colour the tensors according to the specified
``colourImage``. The functions in the :mod:`.gl21.glvector_funcs` module
are used to manage the fragment shader.


The following textures are used for rendering a ``GLTensor`` instance - this
is in addition to the textures that are used for :class:`.GLVector` instances
(of which the ``GLTensor`` is a sub-class):

  ============== ================== ==================
  Attribute name Description        Texture unit
  ============== ================== ==================
  ``v1Texture``  First eigenvector  ``gl.GL_TEXTURE8``
  ``v2Texture``  Second eigenvector ``gl.GL_TEXTURE9``
  ``v3Texture``  Third eigenvector  ``gl.GL_TEXTURE10``
  ``l1Texture``  First eigenvalue   ``gl.GL_TEXTURE11``
  ``l2Texture``  Second eigenvalue  ``gl.GL_TEXTURE12``
  ``l3Texture``  Third eigenvalue   ``gl.GL_TEXTURE13``
  ============== ================== ==================
"""


import numpy                          as np
import numpy.linalg                   as npla
import OpenGL.GL                      as gl
import OpenGL.GL.ARB.draw_instanced   as arbdi

import fsl.utils.transform      as transform
import fsl.fsleyes.gl.resources as glresources
import fsl.fsleyes.gl.routines  as glroutines
import fsl.fsleyes.gl.textures  as textures
import                             glvector_funcs


def init(self):
    """Creates textures for the tensor eigenvalue and eigenvector images,
    and calls :func:`compileShaders` and :func:`updateShaderState`.

    :returns: A list of ``Thread`` instances, one for each of the
             :class:`.ImageTexture` instances that are created. See
             the ``init`` parameter to :meth:`.GLVector.__init__`.
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

    names      = ['v1', 'v2', 'v3', 'l1', 'l2', 'l3']
    imgs       = [ v1,   v2,   v3,   l1,   l2,   l3]
    texThreads = []

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

        texThreads.append(tex.refreshThread())

        setattr(self, '{}Texture'.format(name), tex)

    self.shader = None

    compileShaders(self)
    updateShaderState(self)

    return texThreads


def destroy(self):
    """Deletes the :class:`.GLSLShader`, and all textures. """
    
    self.shader.destroy()
    self.shader = None
    
    names = ['v1', 'v2', 'v3', 'l1', 'l2', 'l3']

    for name in names:
        attrName = '{}Texture'.format(name)
        tex      = getattr(self, attrName)
        
        glresources.delete(tex.getTextureName())
        setattr(self, attrName, None)


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

    shader = self.shader
    opts   = self.displayOpts
    
    shader.load()
    
    changed = glvector_funcs.updateFragmentShaderState(self)

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
    changed |= shader.set('v1Texture', 8)
    changed |= shader.set('v2Texture', 9)
    changed |= shader.set('v3Texture', 10)
    changed |= shader.set('l1Texture', 11)
    changed |= shader.set('l2Texture', 12)
    changed |= shader.set('l3Texture', 13)
    
    changed |= shader.set('v1ValXform', v1ValXform)
    changed |= shader.set('v2ValXform', v2ValXform)
    changed |= shader.set('v3ValXform', v3ValXform)
    changed |= shader.set('l1ValXform', l1ValXform)
    changed |= shader.set('l2ValXform', l2ValXform)
    changed |= shader.set('l3ValXform', l3ValXform)

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
    """Must be called before :func:`draw`. Loads the shader programs, does
    some shader state configuration, and binds textures to texture units.
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
    """Generates voxel coordinates for each tensor to be drawn, does some
    final shader state configuration, and draws the tensors.
    """

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
    shader.setAtt('voxel',           voxels, divisor=1)
    shader.set(   'voxToDisplayMat', xform)
    shader.loadAtts()
    
    arbdi.glDrawElementsInstancedARB(
        gl.GL_QUADS, self.nVertices, gl.GL_UNSIGNED_INT, None, nVoxels)


def postDraw(self):
    """Unloads the shader program, and unbinds the textures. """

    self.shader.unloadAtts()
    self.shader.unload()

    gl.glDisable(gl.GL_CULL_FACE)
    
    self.v1Texture.unbindTexture()
    self.v2Texture.unbindTexture()
    self.v3Texture.unbindTexture()
    self.l1Texture.unbindTexture()
    self.l2Texture.unbindTexture()
    self.l3Texture.unbindTexture()
