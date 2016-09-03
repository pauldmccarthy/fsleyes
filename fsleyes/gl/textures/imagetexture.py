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


from . import texture3d


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


    def __imageDataChanged(self, *a):
        """Called when the :class:`.Image` notifies about a data changes.
        Triggers an image texture refresh via a call to :meth:`set`.
        """
        self.set()

        
    def set(self, **kwargs):
        """Overrides :meth:`.Texture3D.set`. Set any parameters on this
        ``ImageTexture``. This method accepts any parameters that are accepted
        by :meth:`.Texture3D.set`, plus the following:

        ========== ======================
        ``volume`` See :meth:`setVolume`.
        ========== ======================

        :returns: ``True`` if any settings have changed and the
                  ``ImageTexture`` is to be refreshed , ``False`` otherwise.

        """

        kwargs         .pop('data',      None)
        kwargs         .pop('normalise', None)
        volume = kwargs.pop('volume',    self.__volume)

        is4D   = self.__nvals == 1          and \
                 len(self.image.shape) == 4 and \
                 self.image.shape[3] > 1

        if volume is None and self.__volume is None:
            volume = 0

        if not is4D:
            kwargs['data'] = self.image[:]

        elif volume != self.__volume:
            
            self.__volume  = volume
            kwargs['data'] = self.image[..., volume]

        kwargs['normalise'] = self.image.dataRange

        return texture3d.Texture3D.set(self, **kwargs)
