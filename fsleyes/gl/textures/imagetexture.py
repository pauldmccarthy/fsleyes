#!/usr/bin/env python
#
# imagetexture.py - The ImageTexture and ImageTexture2D class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageTexture` and :class:`.ImageTexture2D`
classes, :class:`.Texture3D` and :class:`.Texture2D` classes for storing an
:class:`.Image` instance.
"""


import logging
import collections

import numpy     as np
import OpenGL.GL as gl

import fsl.utils.transform   as transform
import fsl.data.imagewrapper as imagewrapper
from . import                   texture2d
from . import                   texture3d


log = logging.getLogger(__name__)


def createImageTexture(name, image, *args, **kwargs):
    """Creates and returns an appropriate texture type (either
    :class:`ImageTexture` or :class:`ImageTexture2D`) for the given image.
    """

    max3d = gl.glGetInteger(gl.GL_MAX_3D_TEXTURE_SIZE)
    max2d = gl.glGetInteger(gl.GL_MAX_TEXTURE_SIZE)

    def checklim(shape, lim):
        if any([d > lim for d in shape]):
            raise RuntimeError(
                'Cannot create an OpenGL texture for {} - it exceeds '
                'the hardware limits on this platform (2D: {}, 3D: {}'
                .format(max2d, max3d))

    shape = image.shape[:3]
    shape = [d for d in shape if d > 1]

    # force scalar/vector shape to be 2D
    if   len(shape) == 0: shape = [1, 1]
    elif len(shape) == 1: shape = [shape[0], 1]

    if len(shape) == 3: checklim(shape, max3d)
    else:               checklim(shape, max2d)

    if len(shape) == 3: return ImageTexture(  name, image, *args, **kwargs)
    else:               return ImageTexture2D(name, image, *args, **kwargs)


class ImageTextureBase(object):
    """Base class shared by the :class:`ImageTexture` and
    :class:`ImageTexture2D` classes. Contains logic for retrieving a
    specific volume from a 3D + time or 2D + time :class:`.Image`, and
    for retrieving a specific channel from an RGB(A) ``Image``.
    """


    @staticmethod
    def validateShape(image, texnvals, texndims):
        """Called by :meth:`__init__`. Makes sure that the specified texture
        settings (number of dimensions, and number of values per texture
        element) are compatible with the image.

        :arg image:    :class:`.Image`
        :arg texnvals: Number of values per texture element
        :arg texndims: Number of texture dimensions
        :raises:       :exc:`RuntimeError` if the texture properties are not
                       compatible with the image
        """

        imgnvals = image.nvals
        imgndims = len(image.shape)

        # Anything goes for single-
        # valued textures
        if texnvals == 1:
            return

        # For multi-valued 4D textures,
        # the image must have a shape
        # of the form:
        # (x, y, z, [1, [1, [1, [1, ]]]] nvals)
        if imgnvals == 1:
            expShape     = list(image.shape[:3])
            expShape    += [1] * (imgndims - 3)
            expShape[-1] = texnvals
            if list(image.shape) != expShape:
                raise RuntimeError(
                    'Data shape mismatch: texture size {} requested for '
                    'image shape {}'.format(texnvals, image.shape))

        # Or must be a structured, i.e.
        # RGB(A) array with the correct
        # number of values per voxel.
        elif imgnvals != texnvals:
            raise RuntimeError(
                'Data shape mismatch: texture size {} requested for '
                'image with nvals {}'.format(texnvals, imgnvals))


    def __init__(self, image, nvals, ndims):
        """Create an ``ImageTextureBase``

        :arg image: The :class:`.Image`
        :arg nvals: Number of values per texture element
        :arg ndims: Number of texture dimensions
        """

        self.validateShape(image, nvals, ndims)

        self.__name    = 'ImageTextureBase_{}'.format(id(self))
        self.__image   = image
        self.__volume  = None
        self.__channel = None

        self.__image.register(self.__name,
                              self.__imageDataChanged,
                              'data',
                              runOnIdle=True)


    def destroy(self):
        """Must be called when this ``ImageTextureBase`` is no longer needed.
        """
        self.__image.deregister(self.__name, 'data')
        self.__image = None


    @property
    def image(self):
        """Returns the :class:`.Image` managed by this ``ImageTextureBase``.
        """
        return self.__image


    @property
    def volume(self):
        """For :class:`.Image` instances with more than three dimensions,
        specifies the indices for the fourth and above dimensions with which
        to extract the 3D texture data. If the image has four dimensions, this
        may be a scalar, otherwise it must be a sequence of
        (``Image.ndim - 3``) the correct length.
        """
        return self.__volume


    @volume.setter
    def volume(self, volume):
        """Set the current volume. """
        self.set(volume=volume)


    @property
    def channel(self):
        """For :class:`.Image` instances with multiple values per voxel, such
        as ``RGB24`` or ``RGBA32`` images, this option allows the channel
        to be selected.
        """
        return self.__channel


    @channel.setter
    def channel(self, channel):
        """Set the current channel. """
        self.set(channel=channel)


    @property
    def texCoordXform(self):
        """Returns a transformation matrix which can be used to adjust a set of
        3D texture coordinates so they can index the underlying texture, which
        may be 2D.

        This implementation returns an identity matrix, but it is overridden
        by ``ImageTexture2D``.
        """
        return np.eye(4)


    @property
    def invTexCoordXform(self):
        """Returns the inverse of :meth:`texCoordXform`. """
        return transform.invert(self.texCoordXform)


    def shapeData(self, data):
        """Shape the data so that it is ready for use as texture data.

        This implementation returns the data unchanged, but it is overridden
        by ``ImageTexture2D``.
        """
        return data


    def prepareSetArgs(self, **kwargs):
        """Called by sub-classes in their :meth:`.Texture2D.set`/
        :meth:`.Texture3D.set` override.

        Prepares arguments to be passed through to the underlying
        ``set`` method.  This method accepts any parameters that are accepted
        by :meth:`.Texture3D.set`, plus the following:

        =============== ======================================================
        ``volume``      See :meth:`volume`.

        ``channel``     See :meth:`channel`.

        ``volRefresh``  If ``True`` (the default), the texture data will be
                        refreshed even if the ``volume`` and ``channel``
                        parameters haven't changed. Otherwise, if ``volume``
                        and ``channel`` haven't changed, the texture will not
                        be refreshed.
        =============== ======================================================

        :returns: ``True`` if any settings have changed and the
                  ``ImageTexture`` is to be refreshed , ``False`` otherwise.
        """

        kwargs             .pop('data',           None)
        normRange  = kwargs.pop('normaliseRange', None)
        channel    = kwargs.pop('channel',        self.__channel)
        volume     = kwargs.pop('volume',         self.__volume)
        volRefresh = kwargs.pop('volRefresh',     True)
        image      = self.image
        nvals      = self.nvals
        ndims      = image.ndim

        if len(image.shape) == 3: volume  = None
        if image.nvals      == 1: channel = None

        if normRange is None:
            normRange = image.dataRange

        if ndims == 3 or nvals > 1:
            volume = None
        else:
            if volume is None and self.__volume is None:
                volume = [0] * (ndims - 3)

            elif not isinstance(volume, collections.Sequence):
                volume = [volume]

            if len(volume) != ndims - 3:
                raise ValueError('Invalid volume indices for {} '
                                 'dims: {}'.format(ndims, volume))

        if (not volRefresh)           and \
           (volume  == self.__volume) and \
           (channel == self.__channel):
            return kwargs

        self.__volume  = volume
        self.__channel = channel

        data = self.__getData(volume, channel)
        data = self.shapeData(data)

        kwargs['data']           = data
        kwargs['normaliseRange'] = normRange

        return kwargs


    def __getData(self, volume, channel):
        """Extracts data from the :class:`.Image` for use as texture data.

        For textures with multiple values per element (either by volume, or by
        channel), the data is arranged appropriately, i.e. with the value as
        the first dimension.

        :arg volume:  Volume index/indices, for images with more than three
                      dimensions.
        :arg channel: Channel, for RGB(A) images.
        """

        image = self.image
        slc   = [slice(None), slice(None), slice(None)]

        if volume is not None:
            slc += volume

        if channel is None: data = self.image[              tuple(slc)]
        else:               data = self.image.data[channel][tuple(slc)]

        # For single-valued textures,
        # we don't need to do anything
        if self.nvals == 1:
            return data

        # Multi-valued texture with a
        # single-valued 4D image - we
        # assume that each volume
        # corresponds to a channel
        elif image.nvals == 1 and volume is None:
            data = data.transpose((3, 0, 1, 2))

        # Multi-valued RGB(A) texture
        # with a multi-valued image -
        # cast/reshape the image data
        elif image.nvals > 1 and channel is None:
            data = np.ndarray(buffer=data.data,
                              shape=[self.nvals] + list(data.shape),
                              order='F',
                              dtype=np.uint8)

        return data


    def __imageDataChanged(self, image, topic, sliceobj):
        """Called when the :class:`.Image` notifies about a data changes.
        Triggers an image texture refresh via a call to :meth:`set`.

        :arg image:    The ``Image`` instance

        :arg topic:    The string ``'data'``

        :arg sliceobj: Slice object specifying the portion of the image
                       that was changed.
        """

        # If the data change was performed using
        # normal array indexing, we can just replace
        # that part of the image texture.
        if isinstance(sliceobj, tuple):

            # Get the new data, and calculate an
            # offset into the full image from the
            # slice object
            data   = np.array(image[sliceobj])
            offset = imagewrapper.sliceObjToSliceTuple(sliceobj, image.shape)
            offset = [o[0] for o in offset]

            log.debug('{} data changed - refreshing part of '
                      'texture (offset: {}, size: {})'.format(
                          image.name,
                          offset, data.shape))

            self.patchData(data, offset)

        # Otherwise (boolean array indexing) we have
        # to replace the whole image texture.
        else:

            log.debug('{} data changed - refreshing full '
                      'texture'.format(image.name))

            self.set()


class ImageTexture(ImageTextureBase, texture3d.Texture3D):
    """The ``ImageTexture`` class contains the logic required to create and
    manage a 3D texture which represents a :class:`.Image` instance.


    Once created, the :class:`.Image` instance is available as an attribute of
    an ``ImageTexture`` object, called ``image``. See the :class:`.Texture3D`
    documentation for more details.


    For multi-valued (e.g. RGB) textures, the :class:`.Texture3D` class
    requires data to be passed as a ``(C, X, Y, Z)`` array (for ``C`` values).
    If an ``ImageTexture`` is created with an image of type
    ``NIFTI_TYPE_RGB24`` or ``NIFTI_TYPE_RGBA32``, it will take care of
    re-arranging the image data so that it has the shape required by the
    ``Texture3D`` class.
    """


    def __init__(self,
                 name,
                 image,
                 **kwargs):
        """Create an ``ImageTexture``. A listener is added to the
        :attr:`.Image.data` property, so that the texture data can be
        refreshed whenever the image data changes - see the
        :meth:`__imageDataChanged` method.

        :arg name:   A name for this ``imageTexure``.

        :arg image:  The :class:`.Image` instance.

        :arg volume: Initial volume index/indices, for >3D images.

        All other arguments are passed through to the
        :meth:`.Texture3D.__init__` method, and thus used as initial texture
        settings.


        .. note:: The default value of the ``threaded`` parameter is set to
                  the value of :attr:`.fsl.utils.platform.Platform.haveGui`.
        """

        nvals            = kwargs.get('nvals', 1)
        kwargs['nvals']  = nvals
        kwargs['scales'] = image.pixdim[:3]

        ImageTextureBase   .__init__(self, image, nvals, 3)
        texture3d.Texture3D.__init__(self, name, **kwargs)


    def destroy(self):
        """Must be called when this ``ImageTexture`` is no longer needed."""
        texture3d.Texture3D.destroy(self)
        ImageTextureBase   .destroy(self)


    def set(self, **kwargs):
        """Overrides :meth:`.Texture3D.set`.  Passes all arguments through the
        :meth:`prepareSetArgs` method, then passes them on to
        :meth:`.Texture3D.set`.

        :returns: ``True`` if any settings have changed and the
                  ``ImageTexture`` is to be refreshed , ``False`` otherwise.
        """
        return texture3d.Texture3D.set(self, **self.prepareSetArgs(**kwargs))


class ImageTexture2D(ImageTextureBase, texture2d.Texture2D):
    """The ``ImageTexture2D`` class is the 2D analogue of the
    :class:`ImageTexture` class, for managing a 2D texture which represents an
    :class:`.Image` instance.
    """


    def __init__(self,
                 name,
                 image,
                 **kwargs):
        """Create an ``ImageTexture2D``.
        """

        nvals            = kwargs.get('nvals', 1)
        kwargs['nvals']  = nvals
        kwargs['scales'] = image.pixdim[:3]

        ImageTextureBase   .__init__(self, image, nvals, 2)
        texture2d.Texture2D.__init__(self, name, **kwargs)


    def destroy(self):
        """Must be called when this ``ImageTexture2D`` is no longer needed. """
        texture2d.Texture2D.destroy(self)
        ImageTextureBase   .destroy(self)


    @property
    def texCoordXform(self):
        """Overrides :meth:`ImageTextureBase.texCoordXform`. Returns an
        affine matrix which encodes a rotation that maps the two major
        axes of the image voxel coordinate system to the first two axes
        of the texture coordinate system.
        """

        scales  = [1, 1, 1]
        offsets = [0, 0, 0]
        rots    = [0, 0, 0]

        # Here we apply a rotation to the
        # coordinates to force the two major
        # voxel axes to map to the first two
        # texture coordinate axes
        if self.image.shape[0] == 1:
            rots      = [0, -np.pi / 2, -np.pi / 2]
        elif self.image.shape[1] == 1:
            rots      = [-np.pi / 2, 0, 0]
            scales[1] = -1

        return transform.compose(scales, offsets, rots)


    def shapeData(self, data):
        """Overrides :meth:`ImageTexureBase.shapeData`.

        Shapes the data, ensuring that it is compatible with a 2D texture.

        :arg data: numpy array containing the data
        """

        nvals = self.nvals

        # For scalar, 1D or 2D data, we need
        # to make sure the data has a shape
        # compatible with the ImageTexture2D
        if nvals == 1: oldshape = np.array(data.shape)
        else:          oldshape = np.array(data.shape[1:])

        if   np.all(oldshape         == [1, 1, 1]): newshape = ( 1,  1)
        elif np.all(oldshape[1:]     == [1, 1]):    newshape = (-1,  1)
        elif np.all(oldshape[[0, 2]] == [1, 1]):    newshape = (-1,  1)
        elif np.all(oldshape[:2]     == [1, 1]):    newshape = ( 1, -1)
        elif        oldshape[2]      == 1:          newshape = oldshape[:2]
        elif        oldshape[1]      == 1:          newshape = oldshape[[0, 2]]
        elif        oldshape[0]      == 1:          newshape = oldshape[1:]

        if nvals > 1:
            newshape = [nvals] + list(newshape)

        return data.reshape(newshape)


    def set(self, **kwargs):
        """Overrides :meth:`.Texture2D.set`.  Passes all arguments through the
        :meth:`prepareSetArgs` method, then passes them on to
        :meth:`.Texture2D.set`.

        :returns: ``True`` if any settings have changed and the
                  ``ImageTexture`` is to be refreshed , ``False`` otherwise.
        """
        return texture2d.Texture2D.set(self, **self.prepareSetArgs(**kwargs))
