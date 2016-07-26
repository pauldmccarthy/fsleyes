#!/usr/bin/env python
#
# texture3d.py - The Texture3D class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Texture3D` class, which represents a
3D OpenGL texture.
"""


import logging

import numpy               as np
import OpenGL.GL           as gl

import fsl.utils.notifier  as notifier
import fsl.utils.async     as async
import fsl.utils.transform as transform
from . import                 texture
import fsleyes.gl.routines as glroutines


log = logging.getLogger(__name__)


class Texture3D(texture.Texture, notifier.Notifier):
    """The ``Texture3D`` class contains the logic required to create and
    manage a 3D texture.

    A number of texture settings can be configured through the following
    methods:

    .. autosummary::
       :nosignatures:

       set
       refresh
       setData
       setInterp
       setResolution
       setScales
       setPrefilter
       setPrefilterRange
       setNormalise


    .. autosummary::
       :nosignatures: 

       ready
       textureShape
       voxValXform
       invVoxValXform


    When a ``Texture3D`` is created, and when its settings are changed, it may
    need to prepare the data to be passed to OpenGL - for large textures, this
    can be a time consuming process, so this is performed on a separate thread
    using the :mod:`.async` module (unless the ``threaded`` parameter to
    :meth:`__init__` is set to ``False``). The :meth:`ready` method returns
    ``True`` or ``False`` to indicate whether the ``Texture3D`` can be used.

    Furthermore, the ``Texture3D`` class derives from :class:`.Notifier`, so
    listeners can register to be notified when an ``Texture3D`` is ready to
    be used.
    """

    
    def __init__(self,
                 name,                 
                 nvals=1,
                 notify=True,
                 threaded=True,
                 **kwargs):
        """Create a ``Texture3D``.
        
        :arg name:      A unique name for the texture.
        
        :arg nvals:     Number of values per voxel. 
 
        :arg notify:    Passed to the initial call to :meth:`refresh`.

        :arg threaded:  If ``True`` (the default), the texture data will be
                        prepared on a separate thread (on calls to
                        :meth:`refresh`). Otherwise, the texture data is
                        prepared on the calling thread, and the
                        :meth:`refresh` call will block until it has been
                        prepared.

        All other keyword arguments are passed through to the :meth:`set`
        method, and thus used as initial texture settings.
        """

        texture.Texture.__init__(self, name, 3)

        self.__name       = '{}_{}'.format(type(self).__name__, id(self)) 
        self.__nvals      = nvals
        self.__threaded   = threaded

        # All of these texture settings
        # are updated in the set method,
        # called below.
        self.__data           = None
        self.__preparedData   = None
        self.__prefilter      = None
        self.__prefilterRange = None
        self.__resolution     = None
        self.__scales         = None
        self.__interp         = None
        self.__normalise      = None

        # These attributes are modified
        # in the refresh method (which is
        # called via the set method below). 
        self.__ready         = True

        # These attributes are set by the
        # __refresh, __determineTextureType,
        # and __prepareTextureData methods.
        self.__voxValXform    = None
        self.__invVoxValXform = None
        self.__textureShape   = None
        self.__texFmt         = None
        self.__texIntFmt      = None
        self.__texDtype       = None

        # If threading is enabled, texture
        # refreshes are performed with an
        # async.TaskThread.
        if threaded:
            self.__taskThread = async.TaskThread()
            self.__taskName   = '{}_{}_refresh'.format(type(self).__name__,
                                                       id(self))

            self.__taskThread.daemon = True
            self.__taskThread.start()
        else:
            self.__taskThread = None
            self.__taskName   = None

        self.set(refresh=False, **kwargs)
        
        self.__refresh(notify=notify)


    def destroy(self):
        """Must be called when this ``Texture3D`` is no longer needed.
        Deletes the texture handle.
        """

        texture.Texture.destroy(self)
        self.__data         = None
        self.__preparedData = None

        if self.__taskThread is not None:
            self.__taskThread.stop()

        
    def ready(self):
        """Returns ``True`` if this ``Texture3D`` is ready to be used,
        ``False`` otherwise.
        """
        return self.__ready


    def setInterp(self, interp):
        """Sets the texture interpolation - either ``GL_NEAREST`` or
        ``GL_LINEAR``.
        """
        self.set(interp=interp)

        
    def setData(self, data):
        """Sets the texture data - assumed to be a ``numpy`` array. """
        self.set(data=data) 

        
    def setPrefilter(self, prefilter):
        """Sets the prefilter function - texture data is passed through
        this function before being uploaded to the GPU.

        If this function changes the range of the data, you must also
        provide a ``prefilterRange`` function - see :meth:`setPrefilterRange`.
        """
        self.set(prefilter=prefilter)

        
    def setPrefilterRange(self, prefilterRange):
        """Sets the prefilter range function - if the ``prefilter`` function
        changes the data range, this function must be provided. It is passed
        two parameters - the known data minimum and maximum, and must adjust
        these values so that they reflect the adjusted range of the data that
        was passed to the ``prefilter`` function.
        """
        self.set(prefilterRange=prefilterRange) 

        
    def setResolution(self, resolution):
        """Sets the texture data resolution - this value is passed to the
        :func:`.routines.subsample` function, in the
        :meth:`__prepareTextureData` method.
        """
        self.set(resolution=resolution)


    def setScales(self, scales):
        """Sets scaling factors for each axis of the texture data. These values
        are solely used to calculate the sub-sampling rate if the resolution
        (as set by :meth:`setResolution`) is in terms of something other than
        data indices (e.g. :class:`.Image` pixdims).
        """
        self.set(scales=scales)

        
    def setNormalise(self, normalise):
        """Enable/disable normalisation.

        If normalisation is desired, the ``normalise`` parameter must be a
        sequence of two values, containing the ``(min, max)`` normalisation
        range. The data is then normalised to lie in the range ``[0, 1]`` (or
        normalised to the full range, if being stored as integers) before
        being stored.

        Set to ``None`` to disable normalisation.
        """
        self.set(normalise=normalise)


    @property
    def voxValXform(self):
        """Return a transformation matrix that can be used to transform
        values read from the texture back to the original data range.
        """
        return self.__voxValXform

    
    @property
    def invVoxValXform(self):
        """Return a transformation matrix that can be used to transform
        values in the original data range to values as read from the texture.
        """ 
        return self.__invVoxValXform

    
    @property
    def textureShape(self):
        """Return a tuple containing the texture data shape.
        """ 
        return self.__textureShape


    def set(self, **kwargs):
        """Set any parameters on this ``Texture3D``. Valid keyword
        arguments are:

        ================== ==============================================
        ``interp``         See :meth:`setInterp`.
        ``data``           See :meth:`setData`.
        ``prefilter``      See :meth:`setPrefilter`.
        ``prefilterRange`` See :meth:`setPrefilterRange`
        ``resolution``     See :meth:`setResolution`.
        ``scales``         See :meth:`setScales`.
        ``normalise``      See :meth:`setNormalise`.
        ``refresh``        If ``True`` (the default), the :meth:`refresh`
                           function is called (but only if a setting has 
                           changed). 
        ``notify``         Passed through to the :meth:`refresh` method.
        ================== ==============================================

        :returns: ``True`` if any settings have changed and the
                  ``Texture3D`` is to be refreshed , ``False`` otherwise.
        """
        interp         = kwargs.get('interp',         self.__interp)
        prefilter      = kwargs.get('prefilter',      self.__prefilter)
        prefilterRange = kwargs.get('prefilterRange', self.__prefilterRange)
        resolution     = kwargs.get('resolution',     self.__resolution)
        scales         = kwargs.get('scales',         self.__scales)
        normalise      = kwargs.get('normalise',      self.__normalise)
        data           = kwargs.get('data',           None)
        refresh        = kwargs.get('refresh',        True)
        notify         = kwargs.get('notify',         True)

        changed = {'interp'         : interp         != self.__interp,
                   'data'           : data           is not None,
                   'prefilter'      : prefilter      != self.__prefilter,
                   'prefilterRange' : prefilterRange != self.__prefilterRange,
                   'resolution'     : resolution     != self.__resolution,
                   'scales'         : scales         != self.__scales,
                   'normalise'      : normalise      != self.__normalise}

        if self.__ready and (not any(changed.values())):
            return False

        self.__interp         = interp
        self.__normalise      = normalise
        self.__prefilter      = prefilter
        self.__prefilterRange = prefilterRange
        self.__resolution     = resolution
        self.__scales         = scales

        # If the data is of a type which cannot be
        # stored natively as an OpenGL texture, the
        # data must be normalised. See
        # __determineTextureType and __prepareTextureData 
        if data is not None:

            self.__data = data

            if data.dtype not in (np.uint8, np.int8, np.uint16, np.int16):

                # If the caller has not provided
                # a normalisation range, we have
                # to calculate it.
                if self.__normalise is None:
                    self.__normalise = np.nanmin(data), np.nanmax(data)

        refreshData = any((changed['data'],
                           changed['prefilter'],
                           changed['prefilterRange'],
                           changed['resolution'],
                           changed['scales'],
                           changed['normalise']))

        if refresh:
            self.refresh(refreshData=refreshData, notify=notify)
        
        return True

        
    def refresh(self, *args, **kwargs):
        """(Re-)configures the OpenGL texture. 

        .. note:: This method is a wrapper around the :meth:`__refresh` method,
                  which does the real work, and which is not intended to be
                  called from outside the ``Texture3D`` class.
        """

        # The texture is already
        # being refreshed - ignore
        if not self.__ready:
            return

        self.__refresh(*args, **kwargs)
        

    def __refresh(self, *args, **kwargs):
        """(Re-)configures the OpenGL texture.
        
        :arg refreshData:  If ``True`` (the default), the texture data is
                           refreshed.

        :arg notify:       If ``True`` (the default), a notification is
                           triggered via the :class:`.Notifier` base-class,
                           when this ``Texture3D`` has been refreshed, and 
                           is ready to use. Otherwise, the notification is
                           suppressed.

        This method sets an attribute ``__textureShape`` on this ``Texture3D``
        instance, containing the shape of the texture data.

        .. note:: The texture data is generated on a separate thread, using
                  the :func:`.async.run` function. 
        """

        # Don't bother if data
        # hasn't been set
        if self.__data is None:
            return

        refreshData = kwargs.get('refreshData', True)
        notify      = kwargs.get('notify',      True)

        self.__ready = False

        bound = self.isBound()

        # This can take a long time for big
        # data, so we do it in a separate
        # thread using the async module.
        def genData():

            if refreshData:
                self.__determineTextureType()
                self.__prepareTextureData()

        # Once the genData function has finished,
        # we'll configure the texture back on the
        # main thread - OpenGL doesn't play nicely
        # with multi-threading.
        def configTexture():

            if self.__taskThread is not None and \
               self.__taskThread.isQueued(self.__taskName):
                return
            
            data = self.__preparedData

            # It is assumed that, for textures with more than one
            # value per voxel (e.g. RGB textures), the data is
            # arranged accordingly, i.e. with the voxel value
            # dimension the fastest changing
            if len(data.shape) == 4: self.__textureShape = data.shape[1:]
            else:                    self.__textureShape = data.shape

            log.debug('Configuring 3D texture (id {}) for '
                      '{} (data shape: {})'.format(
                          self.getTextureHandle(),
                          self.getTextureName(),
                          self.__textureShape))

            # The image data is flattened, with fortran dimension
            # ordering, so the data, as stored on the GPU, has its
            # first dimension as the fastest changing.
            data = data.flatten(order='F')

            if not bound:
                self.bindTexture()

            # Enable storage of tightly packed data of any size (i.e.
            # our texture shape does not have to be divisible by 4).
            gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

            # set interpolation routine
            interp = self.__interp
            if interp is None:
                interp = gl.GL_NEAREST
                
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_MAG_FILTER,
                               interp)
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_MIN_FILTER,
                               interp)

            # Clamp texture borders to the edge
            # values - it is the responsibility
            # of the rendering logic to not draw
            # anything outside of the image space
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_WRAP_T,
                               gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_WRAP_R,
                               gl.GL_CLAMP_TO_EDGE)

            # create the texture according to
            # the format determined by the
            # _determineTextureType method.
            gl.glTexImage3D(gl.GL_TEXTURE_3D,
                            0,
                            self.__texIntFmt,
                            self.__textureShape[0],
                            self.__textureShape[1],
                            self.__textureShape[2],
                            0,
                            self.__texFmt,
                            self.__texDtype,
                            data)

            if not bound:
                self.unbindTexture()
                
            log.debug('{}({}) is ready to use'.format(
                type(self).__name__, self.getTextureName()))
            
            self.__ready = True

            if notify:
                self.notify()

        if self.__threaded:
            self.__taskThread.enqueue(genData,
                                      taskName=self.__taskName,
                                      onFinish=configTexture)
        else:
            genData()
            configTexture()


    def __determineTextureType(self):
        """Figures out how the texture data should be stored as an OpenGL 3D
        texture.

        
        Regardless of its native data type, the texture data is stored in an
        unsigned integer format. This method figures out the best data type to
        use - if the data is already in an unsigned integer format, it may be
        used as-is. Otherwise, the data needs to be cast and potentially
        normalised before it can be used as texture data.

        
        Internally (e.g. in GLSL shader code), the GPU automatically
        normalises texture data to the range ``[0.0, 1.0]``. This method
        therefore calculates an appropriate transformation matrix, encoding a
        scale and offset, which may be used to transform these normalised
        values back to the raw data values.


        .. note:: OpenGL does different things to 3D texture data depending on
                  its type: unsigned integer types are normalised from
                  ``[0, INT_MAX]`` to ``[0, 1]``.

                  Floating point texture data types are, by default, *clamped*
                  (not normalised), to the range ``[0, 1]``! This could be
                  overcome by using a more recent versions of OpenGL, or by
                  using the ``ARB.texture_rg.GL_R32F`` data format. Here, we
                  simply cast floating point data to an unsigned integer type,
                  normalise it to the appropriate range, and calculate a
                  transformation matrix to transform back to the data range.

        
        This method sets the following attributes on this ``Texture3D``
        instance:

        ==================== ==============================================
        ``__texFmt``         The texture format (e.g. ``GL_RGB``,
                             ``GL_LUMINANCE``, etc).

        ``__texIntFmt``      The internal texture format used by OpenGL for
                             storage (e.g. ``GL_RGB16``, ``GL_LUMINANCE8``,
                             etc).

        ``__texDtype``       The raw type of the texture data (e.g.
                             ``GL_UNSIGNED_SHORT``)
        ==================== ==============================================

        """        

        dtype     = self.__data.dtype
        normalise = self.__normalise is not None

        # Signed data types are a pain in the arse.
        #
        # TODO It would be nice if you didn't have
        # to perform the data conversion/offset
        # for signed types.

        # Texture data type
        if   normalise:          texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.uint8:  texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.int8:   texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.uint16: texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.int16:  texDtype = gl.GL_UNSIGNED_SHORT

        # The texture format
        if   self.__nvals == 1: texFmt = gl.GL_LUMINANCE
        elif self.__nvals == 2: texFmt = gl.GL_LUMINANCE_ALPHA
        elif self.__nvals == 3: texFmt = gl.GL_RGB
        elif self.__nvals == 4: texFmt = gl.GL_RGBA
        else:
            raise ValueError('Cannot create texture representation for '
                             '{} (nvals: {})'.format(dtype, self.__nvals))

        # Internal texture format
        if self.__nvals == 1:
            if   normalise:          intFmt = gl.GL_LUMINANCE16
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16

        elif self.__nvals == 2:
            if   normalise:          intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16_ALPHA16

        elif self.__nvals == 3:
            if   normalise:          intFmt = gl.GL_RGB16
            elif dtype == np.uint8:  intFmt = gl.GL_RGB8
            elif dtype == np.int8:   intFmt = gl.GL_RGB8
            elif dtype == np.uint16: intFmt = gl.GL_RGB16
            elif dtype == np.int16:  intFmt = gl.GL_RGB16
            
        elif self.__nvals == 4:
            if   normalise:          intFmt = gl.GL_RGBA16
            elif dtype == np.uint8:  intFmt = gl.GL_RGBA8
            elif dtype == np.int8:   intFmt = gl.GL_RGBA8
            elif dtype == np.uint16: intFmt = gl.GL_RGBA16
            elif dtype == np.int16:  intFmt = gl.GL_RGBA16 

        # This is all just for logging purposes
        if log.getEffectiveLevel() == logging.DEBUG:

            if   texDtype == gl.GL_UNSIGNED_BYTE:
                sTexDtype = 'GL_UNSIGNED_BYTE'
            elif texDtype == gl.GL_UNSIGNED_SHORT:
                sTexDtype = 'GL_UNSIGNED_SHORT' 
            
            if   texFmt == gl.GL_LUMINANCE:
                sTexFmt = 'GL_LUMINANCE'
            elif texFmt == gl.GL_LUMINANCE_ALPHA:
                sTexFmt = 'GL_LUMINANCE_ALPHA'
            elif texFmt == gl.GL_RGB:
                sTexFmt = 'GL_RGB'
            elif texFmt == gl.GL_RGBA:
                sTexFmt = 'GL_RGBA'
                
            if   intFmt == gl.GL_LUMINANCE8:
                sIntFmt = 'GL_LUMINANCE8'
            elif intFmt == gl.GL_LUMINANCE16:
                sIntFmt = 'GL_LUMINANCE16' 
            elif intFmt == gl.GL_LUMINANCE8_ALPHA8:
                sIntFmt = 'GL_LUMINANCE8_ALPHA8'
            elif intFmt == gl.GL_LUMINANCE16_ALPHA16:
                sIntFmt = 'GL_LUMINANCE16_ALPHA16'
            elif intFmt == gl.GL_RGB8:
                sIntFmt = 'GL_RGB8'
            elif intFmt == gl.GL_RGB16:
                sIntFmt = 'GL_RGB16'
            elif intFmt == gl.GL_RGBA8:
                sIntFmt = 'GL_RGBA8'
            elif intFmt == gl.GL_RGBA16:
                sIntFmt = 'GL_RGBA16' 
            
            log.debug('Texture ({}) is to be stored as {}/{}/{} '
                      '(normalised: {})'.format(
                          self.getTextureName(),
                          sTexDtype,
                          sTexFmt,
                          sIntFmt,
                          normalise))

        self.__texFmt    = texFmt
        self.__texIntFmt = intFmt
        self.__texDtype  = texDtype


    def __prepareTextureData(self):
        """This method prepares and returns the data, ready to be used as GL
        texture data.
        
        This process potentially involves:

          - Resampling to a different resolution (see the
            :func:`.routines.subsample` function). 
        
          - Pre-filtering (see the ``prefilter`` parameter to
            :meth:`__init__`).
        
          - Normalising (if the ``normalise`` parameter to :meth:`__init__`
            was ``True``, or if the data type cannot be used as-is).
        
          - Casting to a different data type (if the data type cannot be used
            as-is).

        This method sets the following attributes on this ``ImageTexture``
        instance:

        ==================== =============================================
        ``__preparedata``    A ``numpy`` array containing the image data,
                             ready to be copied to the GPU. 

        ``__voxValXform``    An affine transformation matrix which encodes 
                             an offset and a scale, which may be used to 
                             transform the texture data from the range 
                             ``[0.0, 1.0]`` to its raw data range.

        ``__invVoxValXform`` Inverse of ``voxValXform``.
        ==================== =============================================
        """

        log.debug('Preparing data for {}({}) - this may take some time '
                  '...'.format(type(self).__name__, self.getTextureName()))

        data  = self.__data
        dtype = data.dtype

        prefilter      = self.__prefilter
        prefilterRange = self.__prefilterRange
        resolution     = self.__resolution
        scales         = self.__scales
        normalise      = self.__normalise is not None

        if normalise: dmin, dmax = self.__normalise
        else:         dmin, dmax = 0, 0


        if normalise                  and \
           prefilter      is not None and \
           prefilterRange is not None:
            dmin, dmax = prefilterRange(dmin, dmax)

        # Offsets/scales which can be used to transform from
        # the texture data (which may be offset or normalised)
        # back to the original voxel data
        if   normalise:          offset =  dmin
        elif dtype == np.uint8:  offset =  0
        elif dtype == np.int8:   offset = -128
        elif dtype == np.uint16: offset =  0
        elif dtype == np.int16:  offset = -32768

        if   normalise:          scale = dmax - dmin
        elif dtype == np.uint8:  scale = 255
        elif dtype == np.int8:   scale = 255
        elif dtype == np.uint16: scale = 65535
        elif dtype == np.int16:  scale = 65535

        # If the data range is 0 (min == max)
        # we just set an identity xform
        if scale == 0:
            voxValXform    = np.eye(4)
            invVoxValXform = np.eye(4)
        else:
            invScale       = 1.0 / scale
            voxValXform    = transform.scaleOffsetXform(scale, offset)
            invVoxValXform = transform.scaleOffsetXform(
                invScale,
                -offset * invScale)

        if resolution is not None:
            data = glroutines.subsample(data, resolution, pixdim=scales)[0]
        
        if prefilter is not None:
            data = prefilter(data)
            
        if normalise:

            if dmax != dmin:
                data = (data - dmin) / float(dmax - dmin)

            data = np.round(data * 65535)
            data = np.array(data, dtype=np.uint16)

        elif dtype == np.uint8:  pass
        elif dtype == np.int8:   data = np.array(data + 128,   dtype=np.uint8)
        elif dtype == np.uint16: pass
        elif dtype == np.int16:  data = np.array(data + 32768, dtype=np.uint16)

        log.debug('Data preparation for {} complete [dtype={}, '
                  'scale={}, offset={}, dmin={}, dmax={}].'.format(
                      self.getTextureName(),
                      data.dtype,
                      scale,
                      offset,
                      dmin,
                      dmax))

        self.__preparedData   = data
        self.__voxValXform    = voxValXform
        self.__invVoxValXform = invVoxValXform
