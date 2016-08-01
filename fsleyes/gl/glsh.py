#!/usr/bin/env python
#
# glsh.py - The GLSH class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLSH` class, a :class:`.GLObject` for
rendering :class:`.Image` overlays which contain fibre orientation
distribution (FOD) spherical harmonic (SH) coefficients.  The ``GLSH`` class
uses functions defined in the :mod:`.gl21.glsh_funcs` module.

:class:`GLSH` instances can only be rendered in OpenGL 2.1 and above.
"""


import               logging

import numpy      as np

import OpenGL.GL  as gl


import fsleyes.gl          as fslgl
import fsleyes.colourmaps  as fslcm
import fsleyes.gl.textures as textures
from . import                 globject


log = logging.getLogger(__name__)


class GLSH(globject.GLImageObject):
    """The ``GLSH`` class is a :class:`.GLObject` for rendering :class:`.Image`
    overlays which contain fibre orientation distribution (FOD) spherical
    harmonic (SH) coefficients.


    This class manages listeners on :class:`.Display` and :class:`.SHOpts`
    instances, and also manages two textures (described below). The rendering
    logic is implemented in the :mod:`.gl21.glsh_funcs` module.


    Each voxel in a FOD image contains coefficients which describe a spherical
    function.  The :meth:`SHOpts.getSHParameters` method returns a numpy array
    which may be used to transform these coefficients into a set of radii which
    can be applied to the vertices of a sphere to visualise the spherical
    function.

    
    These radii are calculated on every call to :meth:`draw` (via the
    :meth:`updateRadTexture` method), and stored in a :class:`.Texture3D`
    instance, which is available as an attribute called ``radTexture``. This
    texture is only 3D out of necessity - it is ultimately interpreted by
    the ``glsh`` vertex shader as a 1D sequence of values, ordered by voxel
    then vertex.


    ``GLSH`` instances also create and manage a :class:`.ColourMapTexture`,
    which may be used to colour FODs by their radius values. The colour map
    is defined by the :attr:`.SHOpts.colourMap` property.

    
    The textures managed by a ``GLSH`` instance are bound to texture units as
    follows:

    
    =============== ==================
    ``radTexture``  ``gl.GL_TEXTURE0``
    ``cmapTexture`` ``gl.GL_TEXTURE1``
    =============== ==================
    """

    def __init__(self, image, display, xax, yax):
        """Create a ``GLSH`` object.


        Creates a :class:`.Texture3D` instance to store vertex radii and a
        :class:`.ColourMapTexture` to store the :attr:`.SHOpts.colourMap`,
        adds property listeners to the :class:`.Display` and :class:`.SHOpts`
        instances, and calls :func:`.glsh_funcs.init`.
        

        :arg image:   The :class:`.Image` instance
        :arg display: The associated :class:`.Display` instance.
        :arg xax:     Horizontal display axis
        :arg yax:     Vertical display axis
        """
        
        globject.GLImageObject.__init__(self, image, display, xax, yax)

        name = self.name

        self.shader      = None
        self.radTexture  = textures.Texture3D('{}_radTexture'.format(name),
                                              threaded=False)
        self.cmapTexture = textures.ColourMapTexture('{}_cm'.format(name))

        self.addListeners()
        self.shResChanged()
        self.cmapUpdate()
        
        fslgl.glsh_funcs.init(self)

        
    def destroy(self):
        """Removes property listeners, destroys textures, and calls
        :func:`.glsh_funcs.destroy`.
        """
        
        self.removeListeners()

        fslgl.glsh_funcs.destroy(self)

        if self.radTexture  is not None: self.radTexture.destroy()
        if self.cmapTexture is not None: self.cmapTexture.destroy() 

        self.radTexture  = None
        self.cmapTexture = None


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to properties of the
        :class:`.Display` and :class:`.SHOpts` instanecs associated with the
        image.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        opts   .addListener('resolution',      name, self.notify)
        opts   .addListener('transform',       name, self.notify)
        
        opts   .addListener('shResolution' ,   name, self.shResChanged,
                            immediate=True)
        opts   .addListener('size',            name, self.updateShaderState)
        opts   .addListener('lighting',        name, self.updateShaderState)
        opts   .addListener('neuroFlip',       name, self.updateShaderState)
        opts   .addListener('radiusThreshold', name, self.notify)

        opts   .addListener('colourMode',      name, self.updateShaderState)
        opts   .addListener('colourMap',       name, self.cmapUpdate)
        opts   .addListener('xColour',         name, self.updateShaderState)
        opts   .addListener('yColour',         name, self.updateShaderState)
        opts   .addListener('zColour',         name, self.updateShaderState)
        display.addListener('alpha',           name, self.cmapUpdate)
        display.addListener('brightness',      name, self.cmapUpdate)
        display.addListener('contrast',        name, self.cmapUpdate)

    
    def removeListeners(self):
        """Called by :meth:`destroy`. Removes listeners added by
        :meth:`addListeners`.
        """ 

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        opts   .removeListener('resolution',      name)
        opts   .removeListener('transform',       name)

        opts   .removeListener('shResolution',    name)
        opts   .removeListener('size',            name)
        opts   .removeListener('lighting',        name)
        opts   .removeListener('neuroFlip',       name)
        opts   .removeListener('radiusThreshold', name)
        
        opts   .removeListener('colourMode',      name)
        opts   .removeListener('colourMap',       name)
        opts   .removeListener('xColour',         name)
        opts   .removeListener('yColour',         name)
        opts   .removeListener('zColour',         name)
        display.removeListener('alpha',           name)
        display.removeListener('brightness',      name)
        display.removeListener('contrast',        name)

        
    def updateShaderState(self, *a):
        """Calls :func:`.glsh_funcs.updateShaderState`. """
        if fslgl.glsh_funcs.updateShaderState(self):
            self.notify()
            return True
        return False


    def cmapUpdate(self, *a):
        """Called when the colour map texture needs to be updated. Updates it,
        and then calls :meth:`updateShaderState`.
        """

        opts    = self.displayOpts
        display = self.display

        # The cmapTexture is used when
        # colouring by radius values,
        # which are assumed to lie between
        # 0.0 and 1.0
        dmin, dmax = fslcm.briconToDisplayRange(
            (0.0, 1.0),
            display.brightness / 100.0,
            display.contrast   / 100.0)

        self.cmapTexture.set(cmap=opts.colourMap,
                             alpha=display.alpha / 100.0,
                             displayRange=(dmin, dmax))

        if not self.updateShaderState():
            self.notify()

        
    def shResChanged(self, *a):
        """Called when the :attr:`.SHOpts.shResolution` property changes.
        Re-loads the SH parameters from disk, and attaches them as an
        attribute called ``shParams``.
        """
        self.shParams = self.displayOpts.getSHParameters()


    def updateRadTexture(self, voxels):
        """Called by :func:`.glsh_funcs.draw`. Updates the radius texture to
        contain radii for the given set of voxels (assumed to be an ``(N, 3)``
        numpy array).

        If :attr:`.SHOpts.radiusThreshold` is greater than 0, any voxels for
        which all radii are less than the threshold are removed from the
        ``voxels`` array.

        This function returns a tuple containing:
        
          - The ``voxels`` array. If ``SHOpts.radiusThreshold == 0``,
            this will be the same as the input. Otherwise, this will
            be a new array with sub-threshold voxels removed.
            If no voxels are to be rendered (all out of bounds, or below
            the radius threshold), this will be an empty list.
        
          - The adjusted shape of the radius texture.
        """

        opts = self.displayOpts
        
        # Remove out-of-bounds voxels
        shape   = self.image.shape[:3]
        x, y, z = voxels.T
        out     = (x <  0)        | \
                  (y <  0)        | \
                  (z <  0)        | \
                  (x >= shape[0]) | \
                  (y >= shape[1]) | \
                  (z >= shape[2])

        x = np.array(x[~out], dtype=np.int32)
        y = np.array(y[~out], dtype=np.int32)
        z = np.array(z[~out], dtype=np.int32)

        # The dot product of the SH parameters with
        # the SH coefficients for a single voxel gives
        # us the radii for every vertex on the FOD
        # sphere. We can calculate the radii for every
        # voxel quickly with a matrix multiplication of
        # the SH parameters with the SH coefficients of
        # *all* voxels.
        params = self.shParams
        coefs  = self.image.nibImage.get_data()[x, y, z, :]
        radii  = np.dot(params, coefs.T)

        # Remove sub-threshold voxels/radii
        if opts.radiusThreshold > 0:
            aboveThres = np.any(radii >= opts.radiusThreshold, axis=0)
            radii      = np.array(radii[:, aboveThres])
            voxels     = np.array(voxels[aboveThres, :])

        # No voxels - nothing to do
        if voxels.shape[0] == 0:
            return [], [0, 0, 0]

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
        radTexShape = np.array([radii.size, 1, 1])
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

        # Resize and reshape the 
        # radius array as needed
        radTexSize = np.prod(radTexShape)
        if radTexSize != radii.size:
            radii.resize(radTexSize)
            
        radii = radii.reshape(radTexShape, order='F')

        # Copy the data to the texture
        self.radTexture.set(data=radii)

        return voxels, radTexShape


    def ready(self):
        """Returns ``True`` if this ``GLSH`` instance is ready to be
        drawn, ``False`` otherwise.
        """
        return self.radTexture.ready()


    def preDraw(self):
        """Binds textures, and calls :func:`.glsh_funcs.preDraw`. """
        
        # The radTexture needs to be bound *last*,
        # because the updateRadTexture method will
        # be called through draw, and if radTexture
        # is not the most recently bound texture,
        # the update will fail.
        self.cmapTexture.bindTexture(gl.GL_TEXTURE1)
        self.radTexture .bindTexture(gl.GL_TEXTURE0)
        
        fslgl.glsh_funcs.preDraw(self)


    def draw(self, zpos, xform=None, bbox=None):
        """Calls :func:`.glsh_funcs.draw`. """
        fslgl.glsh_funcs.draw(self, zpos, xform, bbox)


    def postDraw(self):
        """Unbinds textures, and calls :func:`.glsh_funcs.postDraw`. """
        self.radTexture .unbindTexture()
        self.cmapTexture.unbindTexture()
        fslgl.glsh_funcs.postDraw(self)
