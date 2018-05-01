#!/usr/bin/env python
#
# glsh.py - The GLSH class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLSH` class, a :class:`.GLObject` for
rendering :class:`.Image` overlays which contain spherical harmonic (SH)
coefficients which represent fibre orientation distributions (FODs).  The
``GLSH`` class uses functions defined in the :mod:`.gl21.glsh_funcs` module.

:class:`GLSH` instances can only be rendered in OpenGL 2.1 and above.
"""


import               logging
import               warnings

import numpy      as np

import OpenGL.GL  as gl


import fsleyes.gl          as fslgl
import fsleyes.gl.textures as textures
import fsleyes.gl.glvector as glvector


log = logging.getLogger(__name__)


class GLSH(glvector.GLVectorBase):
    """The ``GLSH`` class is a :class:`.GLVectorBase` for rendering
    :class:`.Image` overlays which contain spherical harmonic (SH) coefficients
    that represent fibre orientation distributions (FOD).


    This class manages listeners on :class:`.Display` and :class:`.SHOpts`
    instances, and also manages two textures (described below). The rendering
    logic is implemented in the :mod:`.gl21.glsh_funcs` module.


    Each voxel in a FOD image contains coefficients which describe a linear
    combination of spherical harmonic functions.  The
    :meth:`SHOpts.getSHParameters` method returns a numpy array which may be
    used to transform these coefficients into a set of radii that can be
    applied to the vertices of a sphere to visualise the spherical
    function. Pre-calculated vertices of tessellated spheres are used, and are
    retrieved via the :meth:`.SHOpts.getVertices` and
    :meth:`.SHOpts.getIndices` methods.


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

    ``vertices``   ``numpy`` array of shape ``(N, 3)`` which comprise a
                   tessellated sphere. The vertex shader will apply
                   the radii to the vertices contained in this array,
                   to form the FODs at every voxel.

    ``indices``    Indices into ``vertices`` defining the faces of the
                   sphere.

    ``nVertices``  Total number of rendered vertices (equal to
                   ``len(indices)``).

    ``vertIdxs``   Indices for each vertex (equal to
                   ``np.arange(vertices.shape[0])``).
    ============== =====================================================
    """


    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLSH`` object.


        Creates a :class:`.Texture3D` instance to store vertex radii, adds
        property listeners to the :class:`.Display` and :class:`.SHOpts`
        instances, and sets up shaders.


        :arg image:       The :class:`.Image` instance
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg canvas:      The canvas doing the drawing.
        :arg threedee:    Set up for 2D or 3D rendering.
        """

        self.shader     = None
        self.radTexture = None

        # These are updated in the
        # __shStateChanged method.
        self.__shParams = None

        # This texture gets updated on
        # draw calls, so we want it to
        # run on the main thread.
        self.radTexture = textures.Texture3D('{}_radTexture'.format(id(self)),
                                             threaded=False)

        # Usin preinit here (see GLVectorBase)
        # because the GLObject init has to be
        # called before compileShaders can be
        # called, and shStateChanged has to be
        # called after everything else is called.
        glvector.GLVectorBase.__init__(
            self,
            image,
            overlayList,
            displayCtx,
            canvas,
            threedee,
            preinit=self.compileShaders,
            init=self.__shStateChanged)


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


    def ready(self):
        """Overrides :class:`.GLVectorBase.ready`. Returns ``True`` when this
        ``GLSH`` is ready to be drawn.
        """
        return self.__shParams is not None \
            and glvector.GLVectorBase.ready(self)


    def addListeners(self):
        """Overrides :meth:`.GLVectorBase.addListeners`.

        Called by :meth:`__init__`. Adds listeners to properties of the
        :class:`.Display` and :class:`.SHOpts` instanecs associated with the
        image.
        """

        glvector.GLVectorBase.addListeners(self)

        opts = self.opts
        name = self.name

        opts.addListener('shResolution' ,   name, self.__shStateChanged,
                         immediate=True)
        opts.addListener('shOrder'      ,   name, self.__shStateChanged,
                         immediate=True)
        opts.addListener('size',            name, self.updateShaderState)
        opts.addListener('lighting',        name, self.updateShaderState)
        opts.addListener('orientFlip',      name, self.updateShaderState)
        opts.addListener('colourMode',      name, self.updateShaderState)
        opts.addListener('radiusThreshold', name, self.notify)
        opts.addListener('normalise',       name, self.notify)


    def removeListeners(self):
        """Overrides :meth:`.GLVectorBase.removeListeners`. Called by
        :meth:`destroy`. Removes listeners added by :meth:`addListeners`.
        """

        glvector.GLVectorBase.removeListeners(self)

        opts = self.opts
        name = self.name

        opts.removeListener('shResolution',    name)
        opts.removeListener('shOrder',         name)
        opts.removeListener('size',            name)
        opts.removeListener('lighting',        name)
        opts.removeListener('orientFlip',      name)
        opts.removeListener('colourMode',      name)
        opts.removeListener('radiusThreshold', name)
        opts.removeListener('normalise',       name)


    def compileShaders(self, *a):
        """Overrides :meth:`.GLVectorBase.compileShaders`. Calls
        :func:`.glsh_funcs.compileShaders`.
        """
        fslgl.glsh_funcs.compileShaders(self)


    def updateShaderState(self, *a, **kwa):
        """Overrides :meth:`.GLVectorBase.updateShaderState`. Calls
        :func:`.glsh_funcs.updateShaderState`.
        """
        alwaysNotify = kwa.pop('alwaysNotify', False)

        if fslgl.glsh_funcs.updateShaderState(self) or alwaysNotify:
            self.notify()
            return True
        return False


    def __shStateChanged(self, *a):
        """Called when the :attr:`.SHOpts.shResolution` property changes.
        Re-loads the SH parameters from disk, and attaches them as an
        attribute called ``__shParams``.
        """

        opts = self.opts

        self.__shParams = opts.getSHParameters()
        self.vertices   = opts.getVertices()
        self.indices    = opts.getIndices()
        self.nVertices  = len(self.indices)
        self.vertIdxs   = np.arange(self.vertices.shape[0], dtype=np.float32)

        self.updateShaderState(alwaysNotify=True)


    def __coefVolumeMask(self):
        """Figures out which volumes from the image need to be included in the
        SH radius calculation. If an image has been generated with a particular
        maximum SH function order, but is being displayed at a reduced order,
        a sub-set of the volumes need to be used in the calculation.


        :returns A ``slice`` object which can be used to select a subset of
                 volumes from the SH image.


        For a symmetric SH image (which only contains SH functions of even
        order), each volume corresponds to

        ======  =============  =====
        Volume  Maximum order  Order
        ------  -------------  -----
        0       0               0
        1       2              -2
        2       2              -1
        3       2               0
        4       2               1
        5       2               2
        6       4              -4
        7       4              -3
        8       4              -2
        9       4              -1
        10      4               0
        11      4               1
        12      4               2
        13      4               3
        14      4               4
        15      6              -6
        ...     ...            ...
        ======  =============  =====


        Asymmetric images (containing SH functions of both even and odd
        order) follow the same pattern:


        ======  =============  =====
        Volume  Maximum order  Order
        ------  -------------  -----
        0       0               0
        1       1              -1
        2       1               0
        3       1               1
        4       2              -2
        5       2              -1
        6       2               0
        7       2               1
        8       2               2
        9       3              -3
        10      3              -2
        11      3              -1
        12      3               0
        13      3               1
        14      3               2
        15      3               3
        16      4              -4
        ...     ...            ...
        ======  =============  =====
        """
        opts      = self.opts
        maxOrder  = opts.maxOrder
        dispOrder = opts.shOrder
        shType    = opts.shType
        nvols     = self.image.shape[3]

        if maxOrder == dispOrder:
            return slice(None)

        if shType == 'sym':
            for o in range(dispOrder + 2, maxOrder + 2, 2):
                nvols -= 2 * o + 1

        elif shType == 'asym':
            for o in range(dispOrder + 1, maxOrder + 1):
                nvols -= 2 * o + 1

        return slice(nvols)


    def updateRadTexture(self, voxels):
        """Called by :func:`.glsh_funcs.draw`. Updates the radius texture to
        contain radii for the given set of voxels (assumed to be an ``(N, 3)``
        numpy array).

        If :attr:`.SHOpts.radiusThreshold` is greater than 0, any voxels for
        which all radii are less than the threshold are removed from the
        ``voxels`` array.

        If :attr:`.SHOpts.normalise` is ``True``, the radii within each voxel
        are normalised to lie between 0 and 0.5, so that they fit within the
        voxel.

        This function returns a tuple containing:

          - The ``voxels`` array. If ``SHOpts.radiusThreshold == 0``,
            this will be the same as the input. Otherwise, this will
            be a new array with sub-threshold voxels removed.
            If no voxels are to be rendered (all out of bounds, or below
            the radius threshold), this will be an empty list.

          - The adjusted shape of the radius texture.
        """

        opts = self.opts

        # Remove out-of-bounds voxels
        shape   = self.image.shape[:3]
        x, y, z = voxels.T
        out     = (x <  0)        | \
                  (y <  0)        | \
                  (z <  0)        | \
                  (x >= shape[0]) | \
                  (y >= shape[1]) | \
                  (z >= shape[2])
        voxels  = np.asarray(voxels[~out, :], dtype=np.uint32)
        x, y, z = voxels.T

        # The dot product of the SH parameters with
        # the SH coefficients for a single voxel gives
        # us the radii for every vertex on the FOD
        # sphere. We can calculate the radii for every
        # voxel quickly with a matrix multiplication of
        # the SH parameters with the SH coefficients of
        # *all* voxels.
        params = self.__shParams
        vols   = self.__coefVolumeMask()
        coefs  = self.image.nibImage.get_data()[x, y, z, vols]
        radii  = np.dot(coefs, params.T)

        # Remove sub-threshold voxels/radii
        if opts.radiusThreshold > 0:
            aboveThres = np.any(radii >= opts.radiusThreshold, axis=1)
            radii      = radii[ aboveThres, :]
            voxels     = voxels[aboveThres, :]

        # No voxels - nothing to do
        if voxels.shape[0] == 0:
            return [], [0, 0, 0]

        # Normalise within voxel if necessary
        if opts.normalise:
            rmin = radii.min(axis=1)
            rmax = radii.max(axis=1)
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')
                radii = ((radii.T - rmin) / (2 * (rmax - rmin))).T

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

        # Resize and reshape the radius array as needed.
        # Radii starts off as a (voxels, vertices) array.
        # We flatten it to 1D (by voxels, i.e. with
        # vertices the fastest changing)
        radii      = radii.reshape(-1)
        radTexSize = np.prod(radTexShape)

        # if the texture size needs to be bigger,
        # create a new array, and copy the radii
        # data into it
        if radTexSize != radii.size:
            tmp = np.zeros(radTexSize, dtype=radii.dtype)
            tmp[:radii.size] = radii
            radii = tmp

        # reshape to the texture size, making
        # sure that the first dimension is the
        # fastest changing (as this is what
        # OpenGL requires). This ensures that
        # the data remains contiguous in memory
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


    def preDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLVectorBase.preDraw`.  Binds textures, and calls
        :func:`.glsh_funcs.preDraw`.
        """

        # The radTexture needs to be bound *last*,
        # because the updateRadTexture method will
        # be called through draw, and if radTexture
        # is not the most recently bound texture,
        # the update will fail.
        glvector.GLVectorBase.preDraw(self, xform, bbox)
        self.radTexture.bindTexture(gl.GL_TEXTURE4)
        fslgl.glsh_funcs.preDraw(self, xform, bbox)


    def draw2D(self, *args, **kwargs):
        """Overrides :meth:`.GLObject.draw`. Calls :func:`.glsh_funcs.draw`.
        """
        fslgl.glsh_funcs.draw2D(self, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Overrides :meth:`.GLObject.draw`. Calls :func:`.glsh_funcs.draw`.
        """
        fslgl.glsh_funcs.draw3D(self, *args, **kwargs)


    def postDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLVectorBase.postDraw`.  Unbinds textures, and
        calls :func:`.glsh_funcs.postDraw`.
        """
        glvector.GLVectorBase.postDraw(self, xform, bbox)
        self.radTexture.unbindTexture()
        fslgl.glsh_funcs.postDraw(self, xform, bbox)
