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

import numpy                              as np
import OpenGL.GL                          as gl
import OpenGL.extensions                  as glexts
import OpenGL.GL.ARB.texture_float        as arbtf

import fsl.utils.notifier                 as notifier
import fsl.utils.memoize                  as memoize
import fsl.utils.async                    as async
import fsl.utils.transform                as transform
from   fsl.utils.platform import platform as fslplatform
import fsleyes_widgets.utils.status       as status

from . import                                texture
import fsleyes.strings                    as strings
import fsleyes.gl.routines                as glroutines


log = logging.getLogger(__name__)

# Used for debugging
GL_TYPE_NAMES = {

    gl.GL_UNSIGNED_BYTE             : 'GL_UNSIGNED_BYTE',
    gl.GL_UNSIGNED_SHORT            : 'GL_UNSIGNED_SHORT',
    gl.GL_FLOAT                     : 'GL_FLOAT',

    gl.GL_RED                       : 'GL_RED',
    gl.GL_LUMINANCE                 : 'GL_LUMINANCE',
    gl.GL_RG                        : 'GL_RG',
    gl.GL_LUMINANCE_ALPHA           : 'GL_LUMINANCE_ALPHA',
    gl.GL_RGB                       : 'GL_RGB',
    gl.GL_RGBA                      : 'GL_RGBA',

    gl.GL_LUMINANCE8                : 'GL_LUMINANCE8',
    gl.GL_LUMINANCE16               : 'GL_LUMINANCE16',
    arbtf.GL_LUMINANCE32F_ARB       : 'GL_LUMINANCE32F',
    gl.GL_R32F                      : 'GL_R32F',

    gl.GL_LUMINANCE8_ALPHA8         : 'GL_LUMINANCE8_ALPHA8',
    gl.GL_LUMINANCE16_ALPHA16       : 'GL_LUMINANCE16_ALPHA16',
    arbtf.GL_LUMINANCE_ALPHA32F_ARB : 'GL_LUMINANCE_ALPHA_32F',
    gl.GL_RG32F                     : 'GL_RG32F',

    gl.GL_RGB8                      : 'GL_RGB8',
    gl.GL_RGB16                     : 'GL_RGB16',
    gl.GL_RGB32F                    : 'GL_RGB32F' ,
    gl.GL_RGBA8                     : 'GL_RGBA8',
    gl.GL_RGBA16                    : 'GL_RGBA16',
    gl.GL_RGBA32F                   : 'GL_RGBA32F'
}


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
                 threaded=None,
                 **kwargs):
        """Create a ``Texture3D``.

        :arg name:      A unique name for the texture.

        :arg nvals:     Number of values per voxel.

        :arg notify:    Passed to the initial call to :meth:`refresh`.

        :arg threaded: If ``True``, the texture data will be prepared on a
                        separate thread (on calls to
                        :meth:`refresh`). If ``False``, the texture data is
                        prepared on the calling thread, and the
                        :meth:`refresh` call will block until it has been
                        prepared.


        All other keyword arguments are passed through to the :meth:`set`
        method, and thus used as initial texture settings.


        .. note:: The default value of the ``threaded`` parameter is set to
                  the value of :attr:`.fsl.utils.platform.Platform.haveGui`.
        """

        if threaded is None:
            threaded = fslplatform.haveGui

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
        self.__normaliseRange = None

        # These attributes are modified
        # in the refresh method (which is
        # called via the set method below).
        self.__ready          = True

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

        callback = kwargs.get('callback', None)

        self.__refresh(notify=notify, callback=callback)


    def destroy(self):
        """Must be called when this ``Texture3D`` is no longer needed.
        Deletes the texture handle.
        """

        texture.Texture.destroy(self)
        self.__data         = None
        self.__preparedData = None

        if self.__taskThread is not None:
            self.__taskThread.stop()


    @classmethod
    @memoize.memoize
    def canUseFloatTextures(cls, nvals=1):
        """Returns ``True`` if this GL environment supports floating
        point textures, ``False`` otherwise. The test is based on the
        availability of the ``ARB_texture_float`` extension.

        :arg nvals: Number of values per voxel

        :returns: A tuple containing:

                    - ``True`` if floating point textures are supported,
                      ``False`` otherwise

                    - The base texture format to use (``None`` if floating
                      point textures are not supported)

                    - The internal texture format to use  (``None`` if
                      floating point textures are not supported)
        """

        # We need the texture_float extension. The
        # texture_rg extension just provides some
        # nicer/more modern data types, but is not
        # necessary.
        floatSupported = glexts.hasExtension('GL_ARB_texture_float')
        rgSupported    = glexts.hasExtension('GL_ARB_texture_rg')

        if not floatSupported:
            return False, None, None

        if rgSupported:
            if   nvals == 1: baseFmt = gl.GL_RED
            elif nvals == 2: baseFmt = gl.GL_RG
            elif nvals == 3: baseFmt = gl.GL_RGB
            elif nvals == 4: baseFmt = gl.GL_RGBA

            if   nvals == 1: intFmt  = gl.GL_R32F
            elif nvals == 2: intFmt  = gl.GL_RG32F
            elif nvals == 3: intFmt  = gl.GL_RGB32F
            elif nvals == 4: intFmt  = gl.GL_RGBA32F

            return True, baseFmt, intFmt

        else:

            if   nvals == 1: baseFmt = gl.GL_LUMINANCE
            elif nvals == 2: baseFmt = gl.GL_LUMINANCE_ALPHA
            elif nvals == 3: baseFmt = gl.GL_RGB
            elif nvals == 4: baseFmt = gl.GL_RGBA

            if   nvals == 1: intFmt  = arbtf.GL_LUMINANCE32F_ARB
            elif nvals == 2: intFmt  = arbtf.GL_LUMINANCE_ALPHA32F_ARB
            elif nvals == 3: intFmt  = gl.GL_RGB32F
            elif nvals == 4: intFmt  = gl.GL_RGBA32F

            return True, baseFmt, intFmt


    @classmethod
    @memoize.memoize
    def getTextureType(cls, normalise, dtype, nvals):
        """Figures out the GL data type, and the base/internal texture
        formats in whihc the specified data should be stored.

        :arg normalise: Whether the data is to be normalised or not
        :arg dtype:     The original data type (e.g. ``np.uint8``)
        :arg nvals:     Number of values per voxel

        :returns: A tuple containing:

                    - The GL data type
                    - The base texture format
                    - The internal texture format
        """
        floatTextures, fFmt, fIntFmt = cls.canUseFloatTextures(nvals)
        isFloat                      = issubclass(dtype.type, np.floating)

        # Signed data types are a pain in the arse.
        # We have to store them as unsigned, and
        # apply an offset.

        # Note: Throughout this method, it is assumed
        #       that if the data type is not supported,
        #       then the normalise flag will have been
        #       set to True. An error will occur if
        #       this is not the case (which would
        #       indicate that the logic in the set()
        #       method is broken).

        # Data type
        if   normalise:          texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.uint8:  texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.int8:   texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.uint16: texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.int16:  texDtype = gl.GL_UNSIGNED_SHORT
        elif floatTextures:      texDtype = gl.GL_FLOAT

        # Base texture format
        if floatTextures and isFloat: texFmt = fFmt
        elif nvals == 1:              texFmt = gl.GL_LUMINANCE
        elif nvals == 2:              texFmt = gl.GL_LUMINANCE_ALPHA
        elif nvals == 3:              texFmt = gl.GL_RGB
        elif nvals == 4:              texFmt = gl.GL_RGBA

        # Internal texture format
        if nvals == 1:
            if   normalise:          intFmt = gl.GL_LUMINANCE16
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16
            elif floatTextures:      intFmt = fIntFmt

        elif nvals == 2:
            if   normalise:          intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif floatTextures:      intFmt = fIntFmt

        elif nvals == 3:
            if   normalise:          intFmt = gl.GL_RGB16
            elif dtype == np.uint8:  intFmt = gl.GL_RGB8
            elif dtype == np.int8:   intFmt = gl.GL_RGB8
            elif dtype == np.uint16: intFmt = gl.GL_RGB16
            elif dtype == np.int16:  intFmt = gl.GL_RGB16
            elif floatTextures:      intFmt = fIntFmt

        elif nvals == 4:
            if   normalise:          intFmt = gl.GL_RGBA16
            elif dtype == np.uint8:  intFmt = gl.GL_RGBA8
            elif dtype == np.int8:   intFmt = gl.GL_RGBA8
            elif dtype == np.uint16: intFmt = gl.GL_RGBA16
            elif dtype == np.int16:  intFmt = gl.GL_RGBA16
            elif floatTextures:      intFmt = fIntFmt

        return texDtype, texFmt, intFmt


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

        If ``normalise=True``, the data is normalised to lie in the range
        ``[0, 1]`` (or normalised to the full range, if being stored as
        integers) before being stored. The data is normalised according to
        the minimum/maximum of the data, or to a normalise range set via
        :meth:`setNormaliseRange`.

        Set to ``False`` to disable normalisation.

        .. note:: If the data is not of a type that can be stored natively
                  as a texture, the data is automatically normalised,
                  regardless of the value specified here.
        """
        self.set(normalise=normalise)


    def setNormaliseRange(self, normaliseRange):
        """Enable/disable normalisation.

        If normalisation is enabled (see :meth:`setNormalise`), or necessary,
        the data is normalised according to either its minimum/maximum, or
        to the range specified via this method.

        This parameter must be a sequence of two values, containing the
        ``(min, max)`` normalisation range. The data is then normalised to
        lie in the range ``[0, 1]`` (or normalised to the full range, if being
        stored as integers) before being stored.

        If ``None``, the data minimum/maximum are calculated and used.
        """
        self.set(normaliseRange=normaliseRange)


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


    def patchData(self, data, offset):
        """This is a shortcut method which can be used to replace part
        of the image texture data without having to regenerate the entire
        texture.

        The :meth:`set` and :meth:`refresh` methods are quite heavyweight, and
        are written in such a way that partial texture updates are not
        possible. This method was added as a hacky workaround to allow
        small parts of the image texture to be quickly updated.

        .. note:: Hopefully, at some stage, I will refactor the ``Texture3D``
                  class to be more flexible. Therefore, this method might
                  disappear in the future.
        """

        data  = self.__realPrepareTextureData(data)[0]
        shape = data.shape
        data  = data.flatten(order='F')

        bound = self.isBound()
        if not bound:
            self.bindTexture()

        gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                           0,
                           offset[0],
                           offset[1],
                           offset[2],
                           shape[0],
                           shape[1],
                           shape[2],
                           self.__texFmt,
                           self.__texDtype,
                           data)

        if not bound:
            self.unbindTexture()

        self.notify()


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
        ``normalise``      See :meth:`setNormalise.`
        ``normaliseRange`` See :meth:`setNormaliseRange`.
        ``refresh``        If ``True`` (the default), the :meth:`refresh`
                           function is called (but only if a setting has
                           changed).
        ``callback``       Optional function which will be called (via
                           :func:`.async.idle`) when the texture has been
                           refreshed. Only called if ``refresh`` is
                           ``True``, and a setting has changed.
        ``notify``         Passed through to the :meth:`refresh` method.
        ================== ==============================================

        :returns: ``True`` if any settings have changed and the
                  ``Texture3D`` is to be refreshed, ``False`` otherwise.
        """

        interp         = kwargs.get('interp',         self.__interp)
        prefilter      = kwargs.get('prefilter',      self.__prefilter)
        prefilterRange = kwargs.get('prefilterRange', self.__prefilterRange)
        resolution     = kwargs.get('resolution',     self.__resolution)
        scales         = kwargs.get('scales',         self.__scales)
        normalise      = kwargs.get('normalise',      None)
        normaliseRange = kwargs.get('normaliseRange', None)
        data           = kwargs.get('data',           None)
        refresh        = kwargs.get('refresh',        True)
        notify         = kwargs.get('notify',         True)
        callback       = kwargs.get('callback',       None)

        changed = {'interp'         : interp         != self.__interp,
                   'data'           : data           is not None,
                   'normalise'      : normalise      is not None,
                   'normaliseRange' : normaliseRange is not None,
                   'prefilter'      : prefilter      != self.__prefilter,
                   'prefilterRange' : prefilterRange != self.__prefilterRange,
                   'resolution'     : resolution     != self.__resolution,
                   'scales'         : scales         != self.__scales}

        if not any(changed.values()):
            return False

        self.__interp         = interp
        self.__prefilter      = prefilter
        self.__prefilterRange = prefilterRange
        self.__resolution     = resolution
        self.__scales         = scales
        self.__normalise      = bool(normalise)
        self.__normaliseRange = normaliseRange

        if data is not None:

            self.__data = data

            # If the data is of a type which cannot
            # be stored natively as an OpenGL texture,
            # and we don't have support for floating
            # point textures, the data must be
            # normalised. See __determineTextureType
            # and __prepareTextureData
            self.__normalise = self.__normalise or \
                               (not self.canUseFloatTextures()[0] and
                                (data.dtype not in (np.uint8,
                                                    np.int8,
                                                    np.uint16,
                                                    np.int16)))

            # If the caller has not provided
            # a normalisation range, we have
            # to calculate it.
            if self.__normalise and self.__normaliseRange is None:

                self.__normaliseRange = np.nanmin(data), np.nanmax(data)
                log.debug('Calculated {} data range for normalisation: '
                          '[{} - {}]'.format(self.__name,
                                             *self.__normaliseRange))

        refreshData = any((changed['data'],
                           changed['prefilter'],
                           changed['prefilterRange'],
                           changed['normaliseRange'] and self.__normalise,
                           changed['resolution'],
                           changed['scales'],
                           changed['normalise']))

        if refresh:
            self.refresh(refreshData=refreshData,
                         notify=notify,
                         callback=callback)

        return True


    def refresh(self, *args, **kwargs):
        """(Re-)configures the OpenGL texture.

        .. note:: This method is a wrapper around the :meth:`__refresh` method,
                  which does the real work, and which is not intended to be
                  called from outside the ``Texture3D`` class.
        """
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

        :arg callback:     Optional function which will be called (via
                           :func:`.async.idle`) when the texture has been
                           refreshed. Only called if ``refresh`` is
                           ``True``, and a setting has changed.

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
        callback    = kwargs.get('callback',    None)

        self.__ready = False

        bound = self.isBound()

        # This can take a long time for big
        # data, so we do it in a separate
        # thread using the async module.
        def genData():

            # Another genData function is
            # already queued - don't run.
            # The TaskThreadVeto error
            # will stop the TaskThread from
            # calling configTexture as well.
            if self.__taskThread is not None and \
               self.__taskThread.isQueued(self.__taskName):
                raise async.TaskThreadVeto()

            if refreshData:
                self.__determineTextureType()
                self.__prepareTextureData()

        # Once the genData function has finished,
        # we'll configure the texture back on the
        # main thread - OpenGL doesn't play nicely
        # with multi-threading.
        def configTexture():
            data = self.__preparedData

            # If destroy() is called, the
            # preparedData will be blanked
            # out.
            if data is None:
                return

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
            #
            # note: The ancient Chromium driver (still
            #       in use by VirtualBox) will improperly
            #       create 3D textures without two calls
            #       (to glTexImage3D and glTexSubImage3D).
            #       If I specify the texture size and set
            #       the data in a single call, it seems to
            #       expect that the data or texture
            #       dimensions always have even size - odd
            #       sized images will be displayed
            #       incorrectly.
            gl.glTexImage3D(gl.GL_TEXTURE_3D,
                            0,
                            self.__texIntFmt,
                            self.__textureShape[0],
                            self.__textureShape[1],
                            self.__textureShape[2],
                            0,
                            self.__texFmt,
                            self.__texDtype,
                            None)
            gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                               0, 0, 0, 0,
                               self.__textureShape[0],
                               self.__textureShape[1],
                               self.__textureShape[2],
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

            if callback is not None:
                callback()


        # Wrap the above functions in a report
        # decorator in case an error occurs
        title = strings.messages[self, 'dataError']
        msg   = strings.messages[self, 'dataError']
        genData       = status.reportErrorDecorator(title, msg)(genData)
        configTexture = status.reportErrorDecorator(title, msg)(configTexture)

        if self.__threaded:

            # Don't queue the texture
            # refresh task twice
            if not self.__taskThread.isQueued(self.__taskName):
                self.__taskThread.enqueue(genData,
                                          taskName=self.__taskName,
                                          onFinish=configTexture)

            # TODO the task is already queued,
            #      but a callback function has been
            #      specified, should you queue the
            #      callback function?

        else:
            genData()
            configTexture()


    def __determineTextureType(self):
        """Figures out how the texture data should be stored as an OpenGL 3D
        texture. This method just figures out the data types which should be
        used to store the data as a texture. Any necessary data conversion/
        transformation is performed by the :meth:`__prepareTextureData`
        method.


        The data can be stored as a GL texture as-is if:

          - it is of type ``uint8`` or ``uint16``

          - it is of type ``float32``, *and* this GL environment has support
            for floating point textures. Support for floating point textures
            is determined by testing for the availability of the
            ``ARB_texture_float`` extension.


        In all other cases, the data needs to be converted to a supported data
        type, and potentially normalised, before it can be used as texture
        data.  If floating point textures are available, the data is converted
        to float32. Otherwise, the data is converted to ``uint16``, and
        normalised to take the full ``uint16`` data range (``0-65535``), and a
        transformation matrix is saved, allowing transformation of this
        normalised data back to its original data range.


        .. note:: OpenGL does different things to 3D texture data depending on
                  its type: unsigned integer types are normalised from
                  ``[0, INT_MAX]`` to ``[0, 1]``.

                  Floating point texture data types are, by default, *clamped*
                  (not normalised), to the range ``[0, 1]``! We can overcome by
                  this by using a true floating point texture, which is
                  accomplished by using one of the data types provided by the
                  ``ARB_texture_float`` extension. If this extension is not
                  available, we have no choice but to normalise the data.


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

        if self.__nvals not in range(1, 5):
            raise ValueError('Cannot create texture representation '
                             'for {} (nvals: {})'.format(self.__data.dtype,
                                                         self.__nvals))

        dtype                    = self.__data.dtype
        normalise                = self.__normalise
        nvals                    = self.__nvals
        texDtype, texFmt, intFmt = self.getTextureType(normalise, dtype, nvals)

        log.debug('Texture ({}) is to be stored as {}/{}/{} '
                  '(normalised: {})'.format(
                      self.getTextureName(),
                      GL_TYPE_NAMES[texDtype],
                      GL_TYPE_NAMES[texFmt],
                      GL_TYPE_NAMES[intFmt],
                      normalise))

        self.__texFmt    = texFmt
        self.__texIntFmt = intFmt
        self.__texDtype  = texDtype


    def __prepareTextureData(self):
        """This method is a wrapper around the
        :meth:`__realPrepareTextureData` method.


        This method passes the stored image data to ``realPrepareTextureData``,
        and then stores references to its return valuesa as attributes on this
        ``ImageTexture`` instance:

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

        data, voxValXform, invVoxValXform = self.__realPrepareTextureData(
            self.__data)

        self.__preparedData   = data
        self.__voxValXform    = voxValXform
        self.__invVoxValXform = invVoxValXform


    def __realPrepareTextureData(self, data):
        """This method prepares and returns the given ``data``, ready to be
        used as GL texture data.

        This process potentially involves:

          - Resampling to a different resolution (see the
            :func:`.routines.subsample` function).

          - Pre-filtering (see the ``prefilter`` parameter to
            :meth:`__init__`).

          - Normalising (if the ``normalise`` parameter to :meth:`__init__`
            was ``True``, or if the data type cannot be used as-is).

          - Casting to a different data type (if the data type cannot be used
            as-is).

        :returns: A tuple containing:

                    - A ``numpy`` array containing the image data, ready to be
                       copied to the GPU.

                    - An affine transformation matrix which encodes an offset
                      and a scale, which may be used to transform the texture
                      data from the range ``[0.0, 1.0]`` to its raw data
                      range.

                    - Inverse of ``voxValXform``.
        """

        log.debug('Preparing data for {}({}) - this may take some time '
                  '...'.format(type(self).__name__, self.getTextureName()))

        dtype         = data.dtype
        floatTextures = self.canUseFloatTextures()

        prefilter      = self.__prefilter
        prefilterRange = self.__prefilterRange
        resolution     = self.__resolution
        scales         = self.__scales
        normalise      = self.__normalise
        normaliseRange = self.__normaliseRange

        if normalise: dmin, dmax = normaliseRange
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
        elif floatTextures:      offset = 0

        if   normalise:          scale = dmax - dmin
        elif dtype == np.uint8:  scale = 255
        elif dtype == np.int8:   scale = 255
        elif dtype == np.uint16: scale = 65535
        elif dtype == np.int16:  scale = 65535
        elif floatTextures:      scale = 1

        # If the data range is 0 (min == max)
        # we just set an identity xform
        if scale == 0:
            voxValXform    = np.eye(4)
            invVoxValXform = np.eye(4)

        # Otherwise we save a transformation
        # from the texture values back to the
        # original data range. Note that if
        # storing floating point data, this
        # will be an identity transform.
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

        # TODO if FLOAT_TEXTURES, you should
        #      save normalised values as float32
        if normalise:

            log.debug('Normalising to range {} - {}'.format(dmin, dmax))

            if dmax != dmin:
                data = np.clip((data - dmin) / float(dmax - dmin), 0, 1)

            data = np.round(data * 65535)
            data = np.array(data, dtype=np.uint16)

        elif dtype == np.uint8:  pass
        elif dtype == np.int8:   data = np.array(data + 128,   dtype=np.uint8)
        elif dtype == np.uint16: pass
        elif dtype == np.int16:  data = np.array(data + 32768, dtype=np.uint16)
        elif floatTextures and data.dtype != np.float32:
            data = np.array(data, dtype=np.float32)

        log.debug('Data preparation for {} complete [dtype={}, '
                  'scale={}, offset={}, dmin={}, dmax={}].'.format(
                      self.getTextureName(),
                      data.dtype,
                      scale,
                      offset,
                      dmin,
                      dmax))

        return data, voxValXform, invVoxValXform
