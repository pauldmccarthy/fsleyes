#!/usr/bin/env python
#
# texture.py - The Texture and Texture2D classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Texture` class, which is the base classes
for all other FSLeyes texture types. See also the :class:`.Texture2D` and
:class:`.Texture3D` classes.
"""


import              logging
import              contextlib
import functools as ft

import numpy                        as np
import OpenGL.GL                    as gl

import fsl.utils.idle               as idle

import fsl.utils.notifier           as notifier
import fsl.transform.affine         as affine
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
from . import data                  as texdata


log = logging.getLogger(__name__)


class TextureBase(object):
    """Base mixin class used by the :class:`Texture` class.

    This class provides logic for texture lifecycle management
    (creation/destruction) and usage.


    .. autosummary::
       :nosignatures:

       name
       handle
       target
       ndim
       nvals
       isBound
       bound
       bindTexture
       unbindTexture


    The :meth:`bound` method (which uses :meth:`bindTexture` and
    :meth:`unbindTexture`) method allows you to bind a texture object to a GL
    texture unit. For example, let's say we have a texture object called
    ``tex``, and we want to configure and use it::

        import OpenGL.GL as gl

        # When we want to use the texture in a
        # scene render, we need to bind it to
        # a texture unit.
        with tex.bound(gl.GL_TEXTURE0):

            # use linear interpolation
            tex.interp = gl.GL_LINEAR

            # ...
            # Do the render
            # ...
    """


    def __init__(self, name, ndims, nvals):
        """Create a ``TextureBase``.

        :arg name:  The name of this texture - should be unique.
        :arg ndims: Number of dimensions - must be 1, 2 or 3.
        :arg nvals: Number of values stored in each texture element.
        """
        if   ndims == 1: ttype = gl.GL_TEXTURE_1D
        elif ndims == 2: ttype = gl.GL_TEXTURE_2D
        elif ndims == 3: ttype = gl.GL_TEXTURE_3D
        else:            raise ValueError('Invalid number of dimensions')

        self.__texture     = int(gl.glGenTextures(1))
        self.__ttype       = ttype
        self.__name        = name
        self.__ndims       = ndims
        self.__nvals       = nvals
        self.__bound       = 0
        self.__textureUnit = None


    def __del__(self):
        """Prints a log message."""

        # log might get deleted before us
        try:
            log.debug('%s.del (%s)', type(self).__name__, id(self))
        except Exception:
            pass


    def destroy(self):
        """Must be called when this ``TextureBase`` is no longer needed.
        Deletes the texture handle.
        """

        log.debug('Deleting %s (%s) for %s: %s',
                  type(self).__name__, id(self),
                  self.__name, self.__texture)

        gl.glDeleteTextures(self.__texture)
        self.__texture = None


    @property
    def name(self):
        """Returns the name of this texture. This is not the GL texture name,
        rather it is the unique name passed into :meth:`__init__`.
        """
        return self.__name


    @property
    def handle(self):
        """Returns the GL texture handle for this texture. """
        return self.__texture


    @property
    def target(self):
        """Returns the type of this texture - ``GL_TEXTURE_1D``,
        ``GL_TEXTURE_2D`` or ``GL_TEXTURE_3D``.
        """
        return self.__ttype


    @property
    def ndim(self):
        """Return the number of dimensions of this texture - 1, 2, or 3. """
        return self.__ndims


    @property
    def nvals(self):
        """Return the number of values stored at each point in this texture.
        """
        return self.__nvals


    def isBound(self):
        """Returns ``True`` if this texture is currently bound, ``False``
        otherwise.

        .. note:: This method assumes that the :meth:`bindTexture` and
                 :meth:`unbindTexture` methods are called in pairs.
        """
        return self.__bound > 0


    @contextlib.contextmanager
    def bound(self, textureUnit=None):
        """Context manager which can be used to bind and unbind this texture,
        instead of manually calling :meth:`bindTexture` and
        :meth:`unbindTexture`

        :arg textureUnit: The texture unit to bind this texture to, e.g.
                          ``GL_TEXTURE0``.
        """
        try:
            self.bindTexture(textureUnit)
            yield
        finally:
            self.unbindTexture()


    def bindTexture(self, textureUnit=None):
        """Activates and binds this texture.

        :arg textureUnit: The texture unit to bind this texture to, e.g.
                          ``GL_TEXTURE0``.
        """

        if self.__bound == 0:

            if textureUnit is not None:
                gl.glActiveTexture(textureUnit)

            gl.glBindTexture(self.__ttype, self.__texture)

            self.__textureUnit = textureUnit

        self.__bound += 1


    def unbindTexture(self):
        """Unbinds this texture. """

        if self.__bound == 1:
            if self.__textureUnit is not None:
                gl.glActiveTexture(self.__textureUnit)

            gl.glBindTexture(self.__ttype, 0)

            self.__textureUnit = None

        self.__bound = max(0, self.__bound - 1)


class TextureSettingsMixin(object):
    """Mixin class used by the :class:`Texture` class.


    This class provides methods to get/set various settings which can
    be used to manipulate the texture. All of the logic which uses
    these settings is in the ``Texture`` class.


    The following settings can be changed:

    .. autosummary::
       :nosignatures:

       interp
       prefilter
       prefilterRange
       normalise
       normaliseRange
       border
       scales
       resolution

    Additional settings can be added via the ``settings`` argument to
    :meth:`__init__`. All settings can be changed via the :meth:`update`
    method.
    """

    def __init__(self, settings=None):
        """Create a ``TextureSettingsMixin``.

        :arg settings: Sequence of additional settings to make available.
        """

        defaults = ['interp',
                    'prefilter', 'prefilterRange',
                    'normalise', 'normaliseRange',
                    'border', 'resolution', 'scales']

        if settings is None: settings = defaults
        else:                settings = defaults + list(settings)

        self.__settings = {s : None for s in settings}


    @property
    def interp(self):
        """Return the current texture interpolation setting - either
        ``GL_NEAREST`` or ``GL_LINEAR``.
        """
        return self.__settings['interp']


    @interp.setter
    def interp(self, interp):
        """Sets the texture interpolation. """
        self.update(interp=interp)


    @property
    def prefilter(self):
        """Return the current prefilter function - texture data is passed
        through this function before being uploaded to the GPU.

        If this function changes the range of the data, you must also
        provide a ``prefilterRange`` function - see :meth:`prefilterRange`.
        """
        return self.__settings['prefilter']


    @prefilter.setter
    def prefilter(self, prefilter):
        """Set the prefilter function """
        self.update(prefilter=prefilter)


    @property
    def prefilterRange(self):
        """Return the current prefilter range function - if the ``prefilter``
        function changes the data range, this function must be provided. It
        is passed two parameters - the known data minimum and maximum, and
        must adjust these values so that they reflect the adjusted range of
        the data that was passed to the ``prefilter`` function.
        """
        return self.__settings['prefilterRange']


    @prefilterRange.setter
    def prefilterRange(self, prefilterRange):
        """Set the prefilter range function. """
        self.update(prefilter=prefilterRange)


    @property
    def normalise(self):
        """Return the current normalisation state.

        If ``normalise=True``, the data is normalised to lie in the range
        ``[0, 1]`` (or normalised to the full range, if being stored as
        integers) before being stored. The data is normalised according to
        the minimum/maximum of the data, or to a normalise range set via
        the :meth:`normaliseRange`.

        Set this to ``False`` to disable normalisation.

        .. note:: If the data is not of a type that can be stored natively
                  as a texture, the data is automatically normalised,
                  regardless of the value specified here.
        """
        return self.__settings['normalise']


    @normalise.setter
    def normalise(self, normalise):
        """Enable/disable normalisation. """
        self.update(normalise=normalise)


    @property
    def normaliseRange(self):
        """Return the current normalise range.

        If normalisation is enabled (see :meth:`normalise`), or necessary,
        the data is normalised according to either its minimum/maximum, or
        to the range specified via this method.

        This parameter must be a sequence of two values, containing the
        ``(min, max)`` normalisation range. The data is then normalised to
        lie in the range ``[0, 1]`` (or normalised to the full range, if being
        stored as integers) before being stored.

        If ``None``, the data minimum/maximum are calculated and used.
        """
        return self.__settings['normaliseRange']


    @normaliseRange.setter
    def normaliseRange(self, normaliseRange):
        """Set the normalise range. """
        self.update(normaliseRange=normaliseRange)


    @property
    def border(self):
        """Return the texture border colour. Set this to a tuple of four values
        in the range 0 to 1, or ``None`` for no border (in which case the
        texture coordinates will be clamped to edges).
        """
        return self.__settings['border']


    @border.setter
    def border(self, border):
        """Return the texture border colour."""
        self.update(border=border)


    @property
    def scales(self):
        """Return the scaling factors for each axis of the texture data.

        These values are solely used to calculate the sub-sampling rate if the
        resolution (as set by :meth:`resolution`) is in terms of something
        other than data indices (e.g. :class:`.Image` pixdims).
        """
        return self.__settings['scales']


    @scales.setter
    def scales(self, scales):
        """Set the texture data axis scaling factors. """
        self.update(scales=scales)


    @property
    def resolution(self):
        """Return the current texture data resolution - this value is passed
        to the :func:`.routines.subsample` function, in the
        :func:`.prepareData` function.
        """
        return self.__settings['resolution']


    @resolution.setter
    def resolution(self, resolution):
        """Set the texture data resolution. """
        self.update(resolution=resolution)


    def update(self, **kwargs):
        """Set any parameters on this ``TextureSettingsMixin``. Valid keyword
        arguments are:

        ================== ==========================
        ``interp``         See :meth:`interp`.
        ``prefilter``      See :meth:`prefilter`.
        ``prefilterRange`` See :meth:`prefilterRange`
        ``normalise``      See :meth:`normalise.`
        ``normaliseRange`` See :meth:`normaliseRange`
        ``border``         See :meth:`border`
        ``scales``         See :meth:`scales`.
        ``resolution``     See :meth:`resolution`
        ================== ==========================

        :returns: A ``dict`` of ``{attr : changed}`` mappings, indicating
                  which properties have changed value.
        """

        changed = {}
        for s in self.__settings.keys():
            oldval             = self.__settings[s]
            newval             = kwargs.get(s, self.__settings[s])
            changed[s]         = oldval != newval
            self.__settings[s] = newval
        return changed


class Texture(notifier.Notifier, TextureBase, TextureSettingsMixin):
    """The ``Texture`` class is the base class for all other texture types in
    *FSLeyes*. This class is not intended to be used directly - use one of the
    sub-classes instead.


    A texture can be bound and unbound via the methods of the
    :class:`TextureBase` class. Various texture settings can be changed
    via the methods of the :class:`TextureSettingsMixin` class. In the majority
    of cases, in order to draw or configure a texture, it needs to be bound
    (although this depends on the sub-class).


    In order to use a texture, at the very least you need to provide some
    data, or specify a type and shape. This can be done either via the
    :meth:`data`/:meth:`shape`/:meth:`dtype` methods, or by the :meth:`set`
    method. If you specify a shape and data type, any previously specified
    data will be lost, and vice versa.


    Calling :meth:`set` will usually cause the texture to be reconfigured and
    refreshed, although you can also force a refresh by calling the
    :meth:`refresh` method directly.


    The following properties can be queried to retrieve information about the
    tetxure; some will return ``None`` until you have provided some data (or
    a shape and type):

    .. autosummary::
       :nosignatures:

       voxValXform
       invVoxValXform
       shape
       dtype
       textureType
       baseFormat
       internalFormat
       data
       preparedData


    When a ``Texture`` is created, and when its settings are changed, it may
    need to prepare the data to be passed to OpenGL - for large textures, this
    can be a time consuming process, so this may be performed on a separate
    thread using the :mod:`.idle` module (unless the ``threaded`` parameter to
    :meth:`__init__` is set to ``False``). The :meth:`ready` method returns
    ``True`` or ``False`` to indicate whether the ``Texture`` is ready to be
    used.


    Furthermore, the ``Texture`` class derives from :class:`.Notifier`, so
    listeners can register to be notified when an ``Texture`` is ready to
    be used.


    For textures with multiple values per voxel, it is assumed that these
    values are indexed with the first dimension of the texture data (as passed
    to :meth:`data` or :meth:`set`).


    ``Texture`` sub-classes (e.g. :class:`.Texture2D`, :class:`.Texture3D`,
    :class:`.ColourMapTexture`) must override the :meth:`doRefresh` method
    such that it performs the GL calls required to configure the textureb.


    See the :mod:`.resources` module for a method of sharing texture resources.
    """


    def __init__(self,
                 name,
                 ndims,
                 nvals,
                 threaded=False,
                 settings=None,
                 textureFormat=None,
                 internalFormat=None,
                 **kwargs):
        """Create a ``Texture``.

        :arg name:           The name of this texture - should be unique.

        :arg ndims:          Number of dimensions - must be 1, 2 or 3.

        :arg nvals:          Number of values stored in each texture element.

        :arg threaded:       If ``True``, the texture data will be prepared on
                             a separate thread (on calls to
                             :meth:`refresh`). If ``False``, the texture data
                             is prepared on the calling thread, and the
                             :meth:`refresh` call will block until it has been
                             prepared.

        :arg settings:       Additional settings to make available through the
                             :class:`TextureSettingsMixin`.

        :arg textureFormat:  Texture format to use - if not specified, this is
                             automatically determined. If specified, an
                             ``internalFormat`` must also be specified.

        :arg internalFormat: Internal texture format to use - if not specified,
                             this is automatically determined.

        All other arguments are passed through to the initial call to
        :meth:`set`.

        .. note:: All subclasses must accept a ``name`` as the first parameter
                  to their ``__init__`` method, and must pass said ``name``
                  through to the :meth:`__init__` method.

        .. note:: In normal cases, the ``textureFormat`` and ``internalFormat``
                  do not need to be specified - they will be automatically
                  determined using the :func:`.data.getTextureType` function.
                  However, there can be instances where a specific texture type
                  needs to be used. In these instances, it is up to the calling
                  code to ensure that the texture data can be coerced into
                  the correct GL data type.
        """

        TextureBase         .__init__(self, name, ndims, nvals)
        TextureSettingsMixin.__init__(self, settings)

        if ((textureFormat is not None) and (internalFormat is     None)) or \
           ((textureFormat is     None) and (internalFormat is not None)):
            raise ValueError('Both textureFormat and internalFormat '
                             'must be specified')

        self.__ready    = False
        self.__threaded = threaded

        # The data, type and shape are
        # refreshed on every call to
        # set or refresh (the former
        # calls the latter)
        self.__data         = None
        self.__dtype        = None
        self.__shape        = None
        self.__preparedData = None

        # The data is refreshed on
        # every call to set or refresh
        # These attributes are set by
        # the __determineTextureType
        # and __prepareTextureData
        # methods (which are called
        # by refresh)
        self.__voxValXform    = None
        self.__invVoxValXform = None

        self.__autoTexFmt     = textureFormat is None
        self.__texFmt         = textureFormat
        self.__texIntFmt      = internalFormat
        self.__texDtype       = None

        # If threading is enabled, texture
        # refreshes are performed with an
        # idle.TaskThread.
        if threaded:
            self.__taskThread = idle.TaskThread()
            self.__taskName   = '{}_{}_refresh'.format(type(self).__name__,
                                                       id(self))

            self.__taskThread.daemon = True
            self.__taskThread.start()
        else:
            self.__taskThread = None
            self.__taskName   = None

        self.set(**kwargs)


    def destroy(self):
        """Must be called when this ``Texture`` is no longer needed.
        """
        TextureBase.destroy(self)

        if self.__taskThread is not None:
            self.__taskThread.stop()

        self.__taskThread   = None
        self.__data         = None
        self.__preparedData = None



    def ready(self):
        """Returns ``True`` if this ``Texture`` is ready to be used,
        ``False`` otherwise.
        """
        return self.__ready


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


    def texCoordXform(self, origShape):
        """Returns a transformation matrix which can be used to adjust a set of
        3D texture coordinates so they can index the underlying texture, which
        may be 2D.

        This implementation returns an identity matrix, but it is overridden
        by the .Texture2D sub-class, which is sometimes used to store 3D image
        data.

        :arg origShape: Original data shape.
        """
        return np.eye(4)


    def invTexCoordXform(self, origShape):
        """Returns the inverse of :meth:`texCoordXform`. """
        return affine.invert(self.texCoordXform(origShape))


    @property
    def shape(self):
        """Return a tuple containing the texture data shape. """
        return self.__shape


    @shape.setter
    def shape(self, shape):
        """Set the texture data shape. """
        return self.set(shape=shape)


    @property
    def dtype(self):
        """Return the ``numpy`` data type of the texture data."""
        return self.__dtype


    @dtype.setter
    def dtype(self, dtype):
        """Set the ``numpy`` data type for the texture data."""
        self.set(dtype=dtype)


    @property
    def textureType(self):
        """Return the texture data type, e.g. ``gl.GL_UNSIGNED_BYTE``. """
        return self.__texDtype


    @property
    def baseFormat(self):
        """Return the base texture format, e.g. ``gl.GL_ALPHA``. """
        return self.__texFmt


    @property
    def internalFormat(self):
        """Return the sized/internal texture format, e.g. ``gl.GL_ALPHA8``. """
        return self.__texIntFmt


    @property
    def data(self):
        """Returns the data that has been passed to the :meth:`set` method. """
        return self.__data


    @data.setter
    def data(self, data):
        """Set the texture data - this get passed through to :meth:`set`. """
        self.set(data=data)


    @property
    def preparedData(self):
        """Returns the prepared data, i.e. the data as it has been copied
        to the GPU.
        """
        return self.__preparedData


    def shapeData(self, data, oldShape=None):
        """Shape the data so that it is ready for use as texture data.

        This implementation returns the data unchanged, but it is overridden
        by the ``Texture2D`` class, which is sometimes used to store 3D image
        data.

        :arg data:     ``numpy`` array containing the data to be shaped
        :arg oldShape: Original data shape, if this is a sub-array. If not
                       provided, taken from ``data``.
        """
        return data


    def set(self, **kwargs):
        """Set any parameters on this ``Texture``. Valid keyword arguments are:

        ================== ==============================================
        ``interp``         See :meth:`.interp`.
        ``data``           See :meth:`.data`.
        ``shape``          See :meth:`.shape`.
        ``dtype``          See :meth:`.dtype`.
        ``prefilter``      See :meth:`.prefilter`.
        ``prefilterRange`` See :meth:`.prefilterRange`
        ``normalise``      See :meth:`.normalise.`
        ``normaliseRange`` See :meth:`.normaliseRange`.
        ``scales``         See :meth:`.scales`.
        ``resolution``     See :meth:`.resolution`.
        ``refresh``        If ``True`` (the default), the :meth:`refresh`
                           function is called (but only if a setting has
                           changed).
        ``callback``       Optional function which will be called (via
                           :func:`.idle.idle`) when the texture has been
                           refreshed. Only called if ``refresh`` is
                           ``True``, and a setting has changed.
        ``notify``         Passed through to the :meth:`refresh` method.
        ================== ==============================================

        :returns: ``True`` if any settings have changed and the
                  ``Texture`` is being/needs to be refreshed, ``False``
                  otherwise.
        """

        changed  = TextureSettingsMixin.update(self, **kwargs)
        data     = kwargs.get('data',     None)
        shape    = kwargs.get('shape',    self.shape)
        dtype    = kwargs.get('dtype',    self.dtype)
        refresh  = kwargs.get('refresh',  True)
        notify   = kwargs.get('notify',   True)
        callback = kwargs.get('callback', None)

        changed['data']  = data  is not None
        changed['shape'] = shape != self.shape
        changed['dtype'] = dtype != self.dtype

        if not any(changed.values()):
            return False

        if data is not None:

            # The dtype attribute is set
            # later in __prepareTextureData,
            # as it may be different from
            # the dtype of the passed-in
            # data
            self.__data  = data
            self.__dtype = None
            dtype        = data.dtype

            # The first dimension is assumed to contain the
            # values, for multi-valued (e.g. RGB) textures
            if self.nvals > 1: self.__shape = data.shape[1:]
            else:              self.__shape = data.shape

        # If the data is of a type which cannot
        # be stored natively as an OpenGL texture,
        # and we don't have support for floating
        # point textures, the data must be
        # normalised. See determineType and
        # prepareData in the data module
        self.normalise = self.normalise or \
            (not texdata.canUseFloatTextures()[0] and
             (dtype not in (np.uint8, np.int8, np.uint16, np.int16)))

        # If the caller has not provided
        # a normalisation range, we have
        # to calculate it.
        if (data is not None) and \
           self.normalise and \
           (self.normaliseRange is None):
            self.normaliseRange = np.nanmin(data), np.nanmax(data)
            log.debug('Calculated %s data range for normalisation: '
                      '[%s - %s]', self.name, *self.normaliseRange)

        elif changed['shape'] or changed['dtype']:
            self.__data  = None
            self.__dtype = dtype
            self.__shape = shape

        refreshData = any((changed['data'],
                           changed['prefilter'],
                           changed['prefilterRange'],
                           changed['normaliseRange'] and self.normalise,
                           changed['resolution'],
                           changed['scales'],
                           changed['normalise']))

        if refresh:
            self.refresh(refreshData=refreshData,
                         notify=notify,
                         callback=callback)

        return True


    def refresh(self, refreshData=True, notify=True, callback=None):
        """(Re-)configures the OpenGL texture.

        :arg refreshData:  If ``True`` (the default), the texture data is
                           refreshed.

        :arg notify:       If ``True`` (the default), a notification is
                           triggered via the :class:`.Notifier` base-class,
                           when this ``Texture3D`` has been refreshed, and
                           is ready to use. Otherwise, the notification is
                           suppressed.

        :arg callback:     Optional function which will be called (via
                           :func:`.idle.idle`) when the texture has been
                           refreshed. Only called if ``refresh`` is
                           ``True``, and a setting has changed.

        .. note:: The texture data may be generated on a separate thread, using
                  the :func:`.idle.run` function. This is controlled by the
                  ``threaded`` parameter,  passed to :meth:`__init__`.
        """

        # Don't bother if data
        # or shape/type hasn't
        # been set
        data  = self.__data
        shape = self.__shape
        dtype = self.__dtype

        # We either need some data, or
        # we need a shape and data type.
        if data is None and (shape is None or dtype is None):
            return

        refreshData  = refreshData and (data is not None)
        self.__ready = False

        # This can take a long time for big
        # data, so we do it in a separate
        # thread using the idle module.
        def genData():

            # Another genData function is
            # already queued - don't run.
            # The TaskThreadVeto error
            # will stop the TaskThread from
            # calling configTexture as well.
            if self.__taskThread is not None and \
               self.__taskThread.isQueued(self.__taskName):
                raise idle.TaskThreadVeto()

            self.__determineTextureType()

            if refreshData:
                self.__prepareTextureData()

        # Once genData is finished, we pass the
        # result (see __prepareTextureData) to
        # the sub-class doRefresh method.
        def doRefresh():

            self.doRefresh()

            self.__ready = True

            if notify:
                self.notify()
            if callback is not None:
                callback()

        # Wrap the above functions in a report
        # decorator in case an error occurs
        title     = strings.messages[self, 'dataError']
        msg       = strings.messages[self, 'dataError']

        # the genData function is called on a separate thread,
        # but doRefresh is called on the idle/mainloop. So we
        # can use the reportErrorDecorator for the latter, but
        # not the former.
        doRefresh    = status.reportErrorDecorator(title, msg)(doRefresh)
        genDataError = ft.partial(status.reportError, title, msg)

        # Run asynchronously if we are
        # threaded, and we have data to
        # prepare - if we don't have
        # data, we run genData on the
        # current thread, because it
        # shouldn't do anything
        if self.__threaded and (data is not None):

            # TODO the task is already queued,
            #      but a callback function has been
            #      specified, should you queue the
            #      callback function?

            # Don't queue the texture
            # refresh task twice
            if not self.__taskThread.isQueued(self.__taskName):
                self.__taskThread.enqueue(genData,
                                          taskName=self.__taskName,
                                          onFinish=doRefresh,
                                          onError=genDataError)

        else:
            genData()
            doRefresh()


    def patchData(self, data, offset):
        """This is a shortcut method which can be used to replace part
        of the image texture data without having to regenerate the entire
        texture.

        The :meth:`set` and :meth:`refresh` methods are quite heavyweight, and
        are written in such a way that partial texture updates are not
        possible. This method allows small parts of the image texture to be
        quickly updated.
        """
        data = np.asarray(data)

        if len(data.shape) < self.ndim:
            newshape = list(data.shape) + [1] * (self.ndim - len(data.shape))
            data     = data.reshape(newshape)

        data = texdata.prepareData(
            data,
            prefilter=self.prefilter,
            prefilterRange=self.prefilterRange,
            resolution=self.resolution,
            scales=self.scales,
            normalise=self.normalise,
            normaliseRange=self.normaliseRange)[0]

        self.doPatch(data, offset)

        self.notify()


    def doRefresh(self):
        """Must be overridden by sub-classes to configure the texture.

        This method is not intended to be called externally - call
        :meth:`refresh` instead.

        This method should use the :meth:`preparedData`, or the :meth:`shape`,
        to configure the texture. Sub-classes can assume that at least one
        of these will not be ``None``.

        If ``preparedData`` is not ``None``, the ``shape`` should be ignored,
        and inferred from ``preparedData``.
        """
        raise NotImplementedError('Must be implemented by subclasses')


    def doPatch(self, data, offset):
        """Must be overridden by sub-classes to quickly update part of
        the texture data.

        This method is not intended to be called externally - call
        :meth:`patchData` instead.
        """
        raise NotImplementedError('Must be implemented by subclasses')


    def __determineTextureType(self):
        """Figures out how the texture data should be stored as an OpenGL
        texture. See the :func:`.data.getTextureType` function.

        This method sets the following attributes on this ``Texture`` instance:

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

        if self.nvals not in (1, 3, 4):
            raise ValueError('Cannot create texture representation for {} '
                             '(nvals: {})'.format(self.dtype, self.nvals))

        if self.__data is None: dtype = self.__dtype
        else:                   dtype = self.__data.dtype

        normalise                = self.normalise
        nvals                    = self.nvals
        texDtype, texFmt, intFmt = texdata.getTextureType(
            normalise, dtype, nvals)

        if not self.__autoTexFmt:
            texFmt = self.__texFmt
            intFmt = self.__texIntFmt

        log.debug('Texture (%s) is to be stored as %s/%s/%s '
                  '(normalised: %s)',
                  self.name,
                  texdata.GL_TYPE_NAMES[texDtype],
                  texdata.GL_TYPE_NAMES[texFmt],
                  texdata.GL_TYPE_NAMES[intFmt],
                  normalise)

        self.__texFmt    = texFmt
        self.__texIntFmt = intFmt
        self.__texDtype  = texDtype


    def __prepareTextureData(self):
        """Prepare the texture data.

        This method passes the stored data to the :func:`.data.prepareData`
        function and then stores references to its return valuesa as
        attributes on this ``Texture`` instance:

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

        data, voxValXform, invVoxValXform = texdata.prepareData(
            self.__data,
            prefilter=self.prefilter,
            prefilterRange=self.prefilterRange,
            resolution=self.resolution,
            scales=self.scales,
            normalise=self.normalise,
            normaliseRange=self.normaliseRange)

        self.__preparedData   = data
        self.__dtype          = data.dtype
        self.__voxValXform    = voxValXform
        self.__invVoxValXform = invVoxValXform
