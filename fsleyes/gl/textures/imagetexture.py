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

        :arg volume: Initial volume, for 4D images.

        All other arguments are passed through to the
        :meth:`.Texture3D.__init__` method, and thus used as initial texture
        settings.
        """

        nvals = kwargs.get('nvals', 1)

        try:
            if nvals > 1 and image.shape[3] != nvals:
                raise RuntimeError()
        except:
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
        """For 4D :class:`.Image` instances, specifies the volume to use
        as the 3D texture data.
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

        if normRange is None:
            normRange = self.image.dataRange

        is4D   = self.__nvals == 1          and \
                 len(self.image.shape) == 4 and \
                 self.image.shape[3] > 1

        if volume is None and self.__volume is None:
            volume = 0

        if (not volRefresh) and volume == self.__volume:
            return

        if not is4D:
            kwargs['data'] = self.image[:]

        else:

            self.__volume  = volume
            kwargs['data'] = self.image[..., volume]

        kwargs['normaliseRange'] = normRange

        return texture3d.Texture3D.set(self, **kwargs)
