#!/usr/bin/env python
#
# selectiontexture.py - The SelectionTexture class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SelectionTexture2D` and
:class:`SelectionTexture3D` classes, :class:`.Texture` types which can be used
to store :class:`~.selection.Selection` instances.

The ``SelectionTexture2D/3D`` classes are used by the :class:`.VoxelSelection`
annotation to display the contents of a ``Selection`` instance.
"""


import logging

import numpy as np

from fsl.transform       import affine
from fsleyes.gl.textures import texture2d
from fsleyes.gl.textures import texture3d
from fsleyes.utils       import lazyimport


log = logging.getLogger(__name__)


gl = lazyimport('OpenGL.GL', f'{__name__}.gl')


class SelectionTextureBase:
    """Base class shared by the :class:`SelectionTexture2D` and
    :class:`SelectionTexture3D`. Manages updates from the
    :class:`~.selection.Selection` object.
    """

    def __init__(self, selection):
        """
        This method must be called *after* :meth:`.Texture.__init__`.
        """
        self.__selection = selection
        selection.register(self.name, self.__selectionChanged)
        self.__selectionChanged(init=True)


    @property
    def selection(self):
        """Returns a reference to the :class:`~.selection.Selection` object.
        """
        return self.__selection


    def destroy(self):
        """Must be called when this ``SelectionTextureBase`` is no longer
        needed. Removes the listener on the
        :attr:`~.selection.Selection.selection` property.
        """
        self.__selection.deregister(self.name)
        self.__selection = None


    def __selectionChanged(self, *a, **kwa):
        """Called when the :attr:`~.selection.Selection.selection` changes.
        Updates the texture data via the :meth:`.Texture.doPatch` method.
        """

        init             = kwa.pop('init', False)
        old, new, offset = self.__selection.getLastChange()
        shape            = self.__selection.shape

        def prepare(data, oldShape=None):
            data = self.shapeData(data, oldShape=oldShape)
            return (data * 255).astype(np.uint8)

        if init or (new is None):
            data = prepare(self.__selection.getSelection(), shape)
            self.set(data=data)
        else:
            data   = prepare(new)
            offset = affine.transform(offset, self.texCoordXform(shape))
            self.doPatch(data, offset)


class SelectionTexture3D(texture3d.Texture3D, SelectionTextureBase):
    """The ``SelectionTexture3D`` class is a :class:`.Texture3D` which can be
    used to store a :class:`~.selection.Selection` instance.  The ``Selection``
    image array is stored as a single channel 3D texture, which is updated
    whenever the :attr:`~.selection.Selection.selection` property changes -
    updates are managed by the :class:`SelectionTextureBase` class.
    """


    def __init__(self, name, selection):
        """Create a ``SelectionTexture3D``.

        :arg name:      A unique name for this ``SelectionTexture3D``.
        :arg selection: The :class:`~.selection.Selection` instance.
        """

        texture3d.Texture3D .__init__(self, name, nvals=1)
        SelectionTextureBase.__init__(self, selection)


    def destroy(self):
        """Must be called when this ``SelectionTexture3D`` is no longer needed.
        Calls the :meth:`.Texture.destroy` method, and removes the listener
        on the :attr:`~.selection.Selection.selection` property.
        """
        texture3d.Texture3D .destroy(self)
        SelectionTextureBase.destroy(self)


class SelectionTexture2D(texture2d.Texture2D, SelectionTextureBase):
    """The ``SelectionTexture2D`` class is a :class:`.Texture2D` which can be
    used to store a :class:`~.selection.Selection` instance.  The ``Selection``
    image array is stored as a single channel 2D texture, which is updated
    whenever the :attr:`~.selection.Selection.selection` property changes -
    updates are managed by the :class:`SelectionTextureBase` class..
    """


    def __init__(self, name, selection):
        """Create a ``SelectionTexture2D``.

        :arg name:      A unique name for this ``SelectionTexture2D``.
        :arg selection: The :class:`~.selection.Selection` instance.
        """

        texture2d.Texture2D .__init__(self, name, nvals=1)
        SelectionTextureBase.__init__(self, selection)


    def destroy(self):
        """Must be called when this ``SelectionTexture2D`` is no longer needed.
        Calls the :meth:`.Texture.destroy` method, and removes the listener
        on the :attr:`~.selection.Selection.selection` property.
        """
        texture2d.Texture2D .destroy(self)
        SelectionTextureBase.destroy(self)
