#!/usr/bin/env python
#
# selectiontexture.py - The SelectionTexture class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SelectionTexture` class, a
:class:`.Texture` type which can be used to store :class:`.Selection`
instances.

The :class:`SelectionTexture` class is used by the :class:`.VoxelSelection`
annotation.
"""

import logging

import numpy     as np
import OpenGL.GL as gl

from . import       texture


log = logging.getLogger(__name__)


class SelectionTexture(texture.Texture):
    """The ``SelectionTexture`` class is a :class:`.Texture` which can be used
    to represent a :class:`.Selection` instance.  The ``Selection`` image array
    is stored as a single channel 3D texture, which is updated whenever the
    :attr:`.Selection.selection` property changes, and whenever the
    :meth:`refresh` method is called.
    """


    def __init__(self, name, selection):
        """Create a ``SelectionTexture``.

        :arg name:      A unique name for this ``SelectionTexture``.

        :arg selection: The :class:`.Selection` instance.
        """

        texture.Texture.__init__(self, name, 3)

        self.__selection = selection

        selection.register(self.getTextureName(), self.__selectionChanged)

        self.__init()
        self.refresh()


    def __init(self):
        """Called by :meth:`__init__`. Configures the GL texture. """

        self.bindTexture()

        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)

        gl.glTexParameterfv(gl.GL_TEXTURE_3D,
                            gl.GL_TEXTURE_BORDER_COLOR,
                            np.array([0, 0, 0, 0], dtype=np.float32))

        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_BORDER)

        shape = self.__selection.getSelection().shape
        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        gl.GL_ALPHA8,
                        shape[0],
                        shape[1],
                        shape[2],
                        0,
                        gl.GL_ALPHA,
                        gl.GL_UNSIGNED_BYTE,
                        None)

        self.unbindTexture()


    def destroy(self):
        """Must be called when this ``SelectionTexture`` is no longer needed.
        Calls the :meth:`.Texture.destroy` method, and removes the listener
        on the :attr:`.Selection.selection` property.
        """
        texture.Texture.destroy(self)
        self.__selection.deregister(self.getTextureName())
        self.__selection = None


    def refresh(self, block=None, offset=None):
        """Refreshes the texture data from the :class:`.Selection` image
        data.

        If ``block`` and ``offset`` are not provided, the entire texture is
        refreshed from the :class:`.Selection` instance. If you know that only
        part of the selection data has changed, you can use the ``block`` and
        ``offset`` arguments to refresh a specific region of the texture
        (which will be faster than a full : refresh).

        :arg block:  A 3D ``numpy`` array containing the new selection data.

        :arg offset: A tuple specifying the ``(x, y, z)`` offset of the
                     ``block`` into the selection array.
        """

        if block is None or offset is None:
            data   = self.__selection.getSelection()
            offset = [0, 0, 0]
        else:
            data = block

        data = data * 255

        log.debug('Updating selection texture (offset {}, size {})'.format(
            offset, data.shape))

        self.bindTexture()
        gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                           0,
                           offset[0],
                           offset[1],
                           offset[2],
                           data.shape[0],
                           data.shape[1],
                           data.shape[2],
                           gl.GL_ALPHA,
                           gl.GL_UNSIGNED_BYTE,
                           data.ravel('F'))
        self.unbindTexture()


    def __selectionChanged(self, *a):
        """Called when the :attr:`.Selection.selection` changes. Updates
        the texture data via the :meth:`refresh` method.
        """

        old, new, offset = self.__selection.getLastChange()

        if new is None:
            data   = self.__selection.getSelection()
            offset = [0, 0, 0]
        else:
            data = new

        self.refresh(data, offset)
