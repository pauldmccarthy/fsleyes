#!/usr/bin/env python
#
# glcsd.py - The GLCSD class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLCSD` class, a :class:`.GLObject` for
rendering :class:`.Image` overlays which contain spherical deconvolution
diffusion model estimates. The ``GLCSD`` class uses functions defined
in the :mod:`.gl21.glcsd_funcs` module.

:class:`GLCSD` instances can only be rendered in OpenGL 2.1 and above.
"""


import os.path    as op
import               logging

import numpy      as np

import OpenGL.GL  as gl


import fsleyes.gl          as fslgl
import fsleyes.gl.textures as textures
from . import                 globject
import                        fsleyes


log = logging.getLogger(__name__)


CSD_TYPE = {
    45 : 'sym',
    81 : 'asym',
}


class GLCSD(globject.GLImageObject):
    """

Creates a :class:`.Texture3D` instance for storing radius values, and
    then 

    ``radTexture`` ``gl.GL_TEXTURE0``
    """

    def __init__(self, image, display, xax, yax):
        """
        """
        
        globject.GLImageObject.__init__(self, image, display, xax, yax)

        self.addListeners()
        self.csdResChanged()

        self.radTexture = textures.Texture3D('{}_radTexture'.format(self.name),
                                             threaded=False)
 

        fslgl.glcsd_funcs.init(self)

        
    def destroy(self):
        
        self.removeListeners()

        fslgl.glcsd_funcs.destroy(self)

        if self.radTexture is not None:
            self.radTexture.destroy()
            self.radTexture = None 
        
 


    def addListeners(self):

        opts = self.displayOpts
        name = self.name

        opts.addListener('csdResolution', name, self.csdResChanged,
                         immediate=True)
        opts.addListener('size',       name, self.updateShaderState)
        opts.addListener('lighting',   name, self.updateShaderState)
        opts.addListener('colourMode', name, self.updateShaderState)
        opts.addListener('neuroFlip',  name, self.updateShaderState)

    
    def removeListeners(self):
        
        opts = self.displayOpts
        name = self.name

        opts.removeListener('csdResolution', name)

        
    def updateShaderState(self, *a):
        if fslgl.glcsd_funcs.updateShaderState(self):
            self.notify()

        
    def csdResChanged(self, *a):

        opts        = self.displayOpts
        order       = self.image.shape[3]
        resolution  = opts.csdResolution ** 2
        fileType    = CSD_TYPE[order]
        
        self.coefficients = np.loadtxt(op.join(
            fsleyes.assetDir,
            'assets',
            'csd',
            '{}x{}_{}.txt'.format(resolution, order, fileType)))


    def updateRadTexture(self, voxels):

        # Remove out-of-bounds voxels
        shape   = self.image.shape[:3]
        x, y, z = voxels.T

        out = (x <  0)        | \
              (y <  0)        | \
              (z <  0)        | \
              (x >= shape[0]) | \
              (y >= shape[1]) | \
              (z >= shape[2])

        x = np.array(x[~out], dtype=np.int32)
        y = np.array(y[~out], dtype=np.int32)
        z = np.array(z[~out], dtype=np.int32)

        # We need to [insert description here when you know more
        #             about the topic].
        # This can be done with a straight matrix multiplication.
        coef  = self.coefficients
        data  = self.image.nibImage.get_data()[x, y, z, :]
        radii = np.dot(coef, data.T).flatten(order='F')

        # The radii are interpreted as a 1D vector
        # containing the radii for every vertex
        # in every voxel. Because we're using an
        # old version of OpenGL (2.1), we can't
        # simply make this 1D vector available
        # to the vertex shader - we need to copy
        # it into a texture, and that texture has
        # to be 3D, because texture dimensions
        # have a maximum size limit.
        #
        # So here we are calculating a suitable
        # 3D shape in which the radius values can
        # be stored. The shape may end up being
        # larger than necessary, if the number of
        # voxels cannot easily be divided/dispersed
        # across the other dimensions.
        radTexShape = np.array(list(radii.shape) + [1, 1])
        maxTexSize  = gl.glGetIntegerv(gl.GL_MAX_3D_TEXTURE_SIZE)
        while np.any(radTexShape > maxTexSize):

            # Find the biggest and smallest dimensions
            imin = np.argmin(radTexShape)
            imax = np.argmax(radTexShape)

            # Try to find a way to move values
            # from the biggest dimension to the
            # smallest dimension
            divisor = 0
            for i in (2, 3, 5, 7):
                if radTexShape[imax] % i == 0:
                    divisor = i
                    break

            # If we can't evenly reshape the texture
            # dimensions, we have to increase the
            # texture size - the radius data will 
            # only take up a portion of the allocated
            # texture size. 
            else:
                divisor            = 2
                radTexShape[imax] += 1

            radTexShape[imax] /= divisor
            radTexShape[imin] *= divisor

        # Resize and reshape the radius
        # array as needed
        radTexSize = np.prod(radTexShape)
        if radTexSize != radii.size:
            radii.resize(radTexSize)
            
        radii = radii.reshape(radTexShape, order='F')

        # Copy the data to the texture
        self.radTexture.set(data=radii)

        return radTexShape


    def ready(self):
        return self.radTexture.ready()


    def preDraw(self):
        self.radTexture.bindTexture(gl.GL_TEXTURE0)
        fslgl.glcsd_funcs.preDraw(self)


    def draw(self, zpos, xform=None, bbox=None):
        fslgl.glcsd_funcs.draw(self, zpos, xform, bbox)


    def postDraw(self):
        self.radTexture.unbindTexture()
        fslgl.glcsd_funcs.postDraw(self)
