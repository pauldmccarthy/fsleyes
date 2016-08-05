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
import fsleyes.gl.routines as glroutines
import fsleyes.gl.textures as textures
import fsleyes.gl.glvector as glvector


log = logging.getLogger(__name__)


class GLSH(glvector.GLVectorBase):
    """The ``GLSH`` class is a :class:`.GLVectorBase` for rendering
    :class:`.Image` overlays which contain fibre orientation distribution
    (FOD) spherical harmonic (SH) coefficients.


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


    The radius texture managed by a ``GLSH`` instance is bound to GL
    texture unit ``GL_TEXTURE4``.


    The following attributes are available on a ``GLSH`` instance (and are
    assumed to be present by the functions in the :mod:`.glsh_funcs` module`):


    ============== =====================================================
    ``radTexture`` :class:`.Texture3D` containing radius values for each
                    vertex to be displayed in the current draw call.
    
    ``vertices``   ``numpy`` array of shape ``(N, 3)`` which comprise
                   a sphere. The vertex shader will apply the radii to
                   the vertices contained in this array, to form the FODs
                   at every voxel.
    
    ``indices``    Indices into ``vertices`` defining the faces of the
                   sphere.
    
    ``nVertices``  Total number of rendered vertices (equal to
                   ``len(indices)``).
    
    ``vertIdxs``   Indices for ecah vertex (equal to
                   ``np.arange(vertices.shape[0])``).
    ============== =====================================================
    """


    def __init__(self, image, display, xax, yax):
        """Create a ``GLSH`` object.


        Creates a :class:`.Texture3D` instance to store vertex radii, adds
        property listeners to the :class:`.Display` and :class:`.SHOpts`
        instances, and calls :func:`.glsh_funcs.init`.
        

        :arg image:   The :class:`.Image` instance
        :arg display: The associated :class:`.Display` instance.
        :arg xax:     Horizontal display axis
        :arg yax:     Vertical display axis
        """
        
        self.shader     = None
        self.radTexture = None

        glvector.GLVectorBase.__init__(
            self,
            image,
            display,
            xax,
            yax,
            init=lambda: fslgl.glsh_funcs.init(self))

        self.__shStateChanged()

        # This texture gets updated on
        # draw calls, so we want it to
        # run on the main thread.
        self.radTexture = textures.Texture3D('{}_radTexture'.format(self.name),
                                             threaded=False)

        
    def destroy(self):
        """Removes property listeners, destroys textures, and calls
        :func:`.glsh_funcs.destroy`.
        """

        self.removeListeners()

        fslgl.glsh_funcs.destroy(self)

        if self.radTexture is not None:
            self.radTexture.destroy()

        self.radTexture = None

        glvector.GLVectorBase.destroy(self)


    def addListeners(self):
        """Overrides :meth:`.GLVectorBase.addListeners`.

        Called by :meth:`__init__`. Adds listeners to properties of the
        :class:`.Display` and :class:`.SHOpts` instanecs associated with the
        image.
        """

        glvector.GLVectorBase.addListeners(self)

        opts = self.displayOpts
        name = self.name

        opts.addListener('resolution',      name, self.notify)
        opts.addListener('shResolution' ,   name, self.__shStateChanged,
                         immediate=True)
        opts.addListener('size',            name, self.updateShaderState)
        opts.addListener('lighting',        name, self.updateShaderState)
        opts.addListener('neuroFlip',       name, self.updateShaderState)
        opts.addListener('radiusThreshold', name, self.notify)
        opts.addListener('colourMode',      name, self.updateShaderState)

    
    def removeListeners(self):
        """Overrides :meth:`.GLVectorBase.removeListeners`. Called by
        :meth:`destroy`. Removes listeners added by :meth:`addListeners`.
        """

        glvector.GLVectorBase.removeListeners(self)

        opts = self.displayOpts
        name = self.name

        opts.removeListener('resolution',      name)
        opts.removeListener('shResolution',    name)
        opts.removeListener('size',            name)
        opts.removeListener('lighting',        name)
        opts.removeListener('neuroFlip',       name)
        opts.removeListener('radiusThreshold', name)
        opts.removeListener('colourMode',      name)


    def compileShaders(self, *a):
        """Overrides :meth:`.GLVectorBase.compileShaders`. Calls
        :func:`.glsh_funcs.compileShaders`.
        """
        fslgl.glsh_funcs.compileShaders(self)

        
    def updateShaderState(self, *a):
        """Overrides :meth:`.GLVectorBase.updateShaderState`. Calls
        :func:`.glsh_funcs.updateShaderState`.
        """
        if fslgl.glsh_funcs.updateShaderState(self):
            self.notify()
            return True
        return False

        
    def __shStateChanged(self, *a):
        """Called when the :attr:`.SHOpts.shResolution` property changes.
        Re-loads the SH parameters from disk, and attaches them as an
        attribute called ``__shParams``.

        Also calls :meth:`__updateVertices`.
        """
        self.__shParams = self.displayOpts.getSHParameters()
        self.__updateVertices()


    def __updateVertices(self):
        """
        """
        
        opts = self.displayOpts
        
        vertices, indices = glroutines.unitSphere(opts.shResolution)

        self.vertices  = vertices
        self.indices   = indices
        self.nVertices = len(indices)
        self.vertIdxs  = np.arange(vertices.shape[0], dtype=np.float32) 


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
        params = self.__shParams
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


    def texturesReady(self):
        """Overrides :meth:`.GLVectorBase.texturesReady`. Returns ``True`` if
        all textures used by this ``GLSH`` instance are ready to be used,
        ``False`` otherwise.
        """
        return (self.radTexture is not None and
                self.radTexture.ready()     and
                glvector.GLVectorBase.texturesReady(self))


    def preDraw(self):
        """Overrides :meth:`.GLVectorBase.preDraw`.  Binds textures, and calls
        :func:`.glsh_funcs.preDraw`.
        """
        
        # The radTexture needs to be bound *last*,
        # because the updateRadTexture method will
        # be called through draw, and if radTexture
        # is not the most recently bound texture,
        # the update will fail.
        glvector.GLVectorBase.preDraw(self)
        self.radTexture.bindTexture(gl.GL_TEXTURE4)
        fslgl.glsh_funcs.preDraw(self)


    def draw(self, zpos, xform=None, bbox=None):
        """Overrides :meth:`.GLObject.draw`. Calls :func:`.glsh_funcs.draw`.
        """
        fslgl.glsh_funcs.draw(self, zpos, xform, bbox)


    def postDraw(self):
        """Overrides :meth:`.GLVectorBase.postDraw`.  Unbinds textures, and
        calls :func:`.glsh_funcs.postDraw`.
        """
        glvector.GLVectorBase.postDraw(self)
        self.radTexture.unbindTexture()
        fslgl.glsh_funcs.postDraw(self)
