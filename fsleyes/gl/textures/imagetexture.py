#!/usr/bin/env python
#
# imagetexture.py - The ImageTexture class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageTexture` class, a :class:`.Texture3D`
for storing a :class:`.Image` instance.
"""


import logging
import collections

import numpy as np

from . import texture3d
import fsl.data.imagewrapper as imagewrapper


log = logging.getLogger(__name__)


class ImageTexture(texture3d.Texture3D):
    """The ``ImageTexture`` class contains the logic required to create and
    manage a 3D texture which represents a :class:`.Image` instance.

    Once created, the :class:`.Image` instance is available as an attribute
    of an ``ImageTexture`` object, called ``image``. See the
    :class:`.Texture3D`
    documentation for more details.
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
        """

        nvals = kwargs.get('nvals', 1)

        # For 4D textures, the image must have a shape of the form:
        #   (x, y, z, [1, [1, [1, [1, ]]]] nvals)
        if nvals > 1:
            ndims        = image.ndim
            expShape     = list(image.shape[:3])
            expShape    += [1] * (ndims - 3)
            expShape[-1] = nvals
            if list(image.shape) != expShape:
                raise RuntimeError('Data shape mismatch: texture '
                                   'size {} requested for '
                                   'image shape {}'.format(nvals, image.shape))

        self.__name       = '{}_{}'.format(type(self).__name__, id(self))
        self.image        = image
        self.__nvals      = nvals
        self.__volume     = None

        kwargs['scales'] = image.pixdim[:3]

        texture3d.Texture3D.__init__(self, name, **kwargs)
        self.image.register(self.__name,
                            self.__imageDataChanged,
                            'data',
                            runOnIdle=True)


    def destroy(self):
        """Must be called when this ``ImageTexture`` is no longer needed.
        Deletes the texture handle, and removes the listener on the
        :attr:`.Image.data` property.
        """

        texture3d.Texture3D.destroy(self)
        self.image.deregister(self.__name, 'data')


    def setVolume(self, volume):
        """For :class:`.Image` instances with more than three dimensions,
        specifies the indices for the fourth and above dimensions with which
        to extract the 3D texture data. If the image has four dimensions, this
        may be a scalar, otherwise it must be a sequence of
        (``Image.ndim - 3``) the correct length.
        """
        self.set(volume=volume)


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


    def set(self, **kwargs):
        """Overrides :meth:`.Texture3D.set`. Set any parameters on this
        ``ImageTexture``. This method accepts any parameters that are accepted
        by :meth:`.Texture3D.set`, plus the following:

        =============== ======================================================
        ``volume``      See :meth:`setVolume`.

        ``volRefresh``  If ``True`` (the default), the texture data will be
                        refreshed even if the ``volume`` parameter hasn't
                        changed. Otherwise, if ``volume`` hasn't changed,
                        the texture will not be refreshed.
        =============== ======================================================

        :returns: ``True`` if any settings have changed and the
                  ``ImageTexture`` is to be refreshed , ``False`` otherwise.
        """

        kwargs             .pop('data',           None)
        normRange  = kwargs.pop('normaliseRange', None)
        volume     = kwargs.pop('volume',         self.__volume)
        volRefresh = kwargs.pop('volRefresh',     True)
        image      = self.image
        nvals      = self.__nvals
        ndims      = image.ndim

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

        if (not volRefresh) and volume == self.__volume:
            return

        self.__volume = volume

        slc = [slice(None), slice(None), slice(None)]
        if volume is not None:
            slc += volume

        kwargs['data']           = self.image[tuple(slc)]
        kwargs['normaliseRange'] = normRange

        return texture3d.Texture3D.set(self, **kwargs)
