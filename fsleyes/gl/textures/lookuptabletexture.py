#!/usr/bin/env python
#
# lookuptabletexture.py - The LookupTableTexture class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LookupTableTexture` class, a 1D
:class:`.Texture` which stores the colours of a :class:`.LookupTable`
as an OpenGL texture.
"""

import logging

import OpenGL.GL as gl
import numpy     as np

import fsleyes.colourmaps as fslcmaps
from . import                texture


log = logging.getLogger(__name__)


class LookupTableTexture(texture.Texture):
    """The ``LookupTableTexture`` class is a 1D :class:`.Texture` which stores
    the colours of a :class:`.LookupTable` as an OpenGL texture.


    A :class:`.LookupTable` stores a collection of label values (assumed to be
    unsigned 16 bit integers), and colours associated with each label. This
    mapping of ``{label : colour}`` is converted into a ``numpy`` array
    of size :math:`max(labels)\\times 3` containing the lookup table, where
    a label value can be used as an array index to retrieve the corresponding
    colour. All aspects of a ``LookupTableTexture`` can be configured via the
    :meth:`set` method.


    As OpenGL textures are indexed by coordinates in the range ``[0.0, 1.0]``,
    you will need to divide label values by :math:`max(labels)` to convert
    them into texture coordinates.

    .. note:: Currently, the maximum label value in a lookup table cannot be
              greater than the maximum size of an OpenGL texture - this limit
              differs between platforms. In the future, if this class needs
              to be modified to support larger lookup tables, it will need to
              be changed to use a 2D texture, and users will need to
              ravel/unravel texture indices between 1D and 2D coordinates.
    """

    def __init__(self, name):
        """Create a ``LookupTableTexture``.

        :arg name: A uniqe name for this ``LookupTableTexture``.
        """

        self.__lut        = None
        self.__alpha      = None
        self.__brightness = None
        self.__contrast   = None

        texture.Texture.__init__(self, name, 1, 4)


    def set(self, **kwargs):
        """Set any parameters on this ``LookupTableTexture``. Valid
        keyword arguments are:

        ============== ======================================================
        ``lut``        The :class:`.LookupTable` instance.
        ``alpha``      Transparency, a value between 0.0 and 1.0. Defaults to
                       1.0
        ``brightness`` Brightness, a value between 0.0 and 1.0. Defaults to
                       0.5.
        ``contrast``   Contrast, a value between 0.0 and 1.0. Defaults to
                       0.5.
        ============== ======================================================
        """

        lut        = kwargs.get('lut',        self)
        alpha      = kwargs.get('alpha',      self)
        brightness = kwargs.get('brightness', self)
        contrast   = kwargs.get('contrast',   self)

        if lut        is not self: self.__lut        = lut
        if alpha      is not self: self.__alpha      = alpha
        if brightness is not self: self.__brightness = brightness
        if contrast   is not self: self.__contrast   = contrast

        self.__refresh()


    def refresh(self):
        """Forces a refresh of this ``LookupTableTexture``. This method should
        be called when the :class:`.LookupTable` has changed, so that the
        underlying texture is kept consistent with it.
        """
        self.__refresh()


    def __refresh(self, *a):
        """Configures the underlying OpenGL texture. """

        lut        = self.__lut
        alpha      = self.__alpha
        brightness = self.__brightness
        contrast   = self.__contrast

        if lut is None:
            return

        if brightness is None: brightness = 0.5
        if contrast   is None: contrast   = 0.5

        # Enough memory is allocated for the lut texture
        # so that shader programs can use label values
        # as indices into the texture. Not very memory
        # efficient, but greatly reduces complexity.
        nvals  = lut.max() + 1
        data   = np.zeros((nvals, 4), dtype=np.uint8)

        for lbl in lut:

            value  = lbl.value
            colour = fslcmaps.applyBricon(lbl.colour, brightness, contrast)

            data[value, :3] = [np.floor(c * 255) for c in colour[:3]]

            if not lbl.enabled:     data[value, 3] = 0
            elif alpha is not None: data[value, 3] = 255 * alpha
            else:                   data[value, 3] = 255

        data = data.ravel('C')

        self.bindTexture()

        # Values out of range are clipped
        gl.glTexParameterfv(gl.GL_TEXTURE_1D,
                            gl.GL_TEXTURE_BORDER_COLOR,
                            np.array([0, 0, 0, 0], dtype=np.float32))
        gl.glTexParameteri( gl.GL_TEXTURE_1D,
                            gl.GL_TEXTURE_WRAP_S,
                            gl.GL_CLAMP_TO_BORDER)

        # Nearest neighbour interpolation
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)

        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        nvals,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        data)
        self.unbindTexture()
