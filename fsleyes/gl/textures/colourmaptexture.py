#!/usr/bin/env python
#
# colourmaptexture.py - The ColourMapTexture class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourMapTexture` class, a 1D
:class:`.Texture` which can be used to store a RGBA colour map.
"""


import logging
import collections.abc as abc

import numpy     as np
import OpenGL.GL as gl

from . import texture


log = logging.getLogger(__name__)


class ColourMapTexture(texture.Texture):
    """The ``ColourMapTexture`` class is a :class:`.Texture` which stores
    a RGB or RGBA colour map.

    A ``ColourMapTexture`` maps a data range to to a colour map. The data
    range may be specified by the :meth:`setDisplayRange` method, and the
    colour map by the :meth:`setColourMap` method. Alternately, both can
    be specified with the :meth:`set` method.


    In OpenGL, textures are indexed with a number between 0.0 and 1.0. So
    in order to map the data range to texture coordinates, an offset/scale
    transformation must be applied to data values. The ``ColourMapTexture``
    calculates this transformation, and makes it available via the
    :meth:`getCoordinateTransform` method.


    The colour map itself can be specified in a number of ways:

      - A ``numpy`` array of size :math:`N\\times 3` or :math:`N\\times 4`,
        containing RGB or RGBA colour values, with colour values in the range
        ``[0, 1]``.

      - A function which accepts an array of values in the range ``[0, 1]``,
        and returns an array of size :math:`N\\times 3` or :math:`N\\times 4`,
        specifying the RGB/RGBA colours that correspond to the input values.


    Some other methods are provided, for configuring the colour map:

    .. autosummary::
       :nosignatures:

       setAlpha
       setInvert
       setResolution
       setGamma
       setInterp
       setBorder
    """


    def __init__(self, name):
        """Create a ``ColourMapTexture``.

        :arg name: A unique name for this ``ColourMapTexture``.
        """

        texture.Texture.__init__(self, name, 1)

        self.__resolution   = None
        self.__cmap         = None
        self.__invert       = False
        self.__interp       = None
        self.__gamma        = None
        self.__alpha        = None
        self.__displayRange = None
        self.__border       = None
        self.__coordXform   = None


    def setColourMap(self, cmap):
        """Set the colour map stored by the ``ColourMapTexture``.

        :arg cmap: The colour map, either a ``numpy`` array of size
                   :math:`N\\times 3` or :math:`N\\times 4`, specifying
                   RGB/RGBA colours, or a function which accepts values
                   in the range ``[0, 1]``, and generates corresponding
                   RGB/RGBA colours.
        """
        self.set(cmap=cmap)


    def setResolution(self, res):
        """Set the resolution (number of colours) of this ``ColourMapTexture``.
        This setting is only applicable when the colour map is specified as a
        function (see :meth:`setColourMap`).
        """
        self.set(resolution=res)


    def setAlpha(self, alpha):
        """Set the transparency of all colours in the colour map. This setting
        is only applicable when the colour map is specified as RGB values.
        """
        self.set(alpha=alpha)


    def setInvert(self, invert):
        """Invert the values in the colour map. """
        self.set(invert=invert)


    def setGamma(self, gamma):
        """Gamma correction - uses ``gamma`` as an exponent to weight the
        colour map towards the low or high end. Only applied if the
        colour map (see :meth:`setColourMap`) is specified as a function.
        """
        self.set(gamma=gamma)


    def setInterp(self, interp):
        """Set the interpolation used by this ``ColourMapTexture`` - either
        ``GL_NEAREST`` or ``GL_LINEAR``.
        """
        self.set(interp=interp)


    def setDisplayRange(self, drange):
        """Set the data range which corresponds to the colours stored in this
        ``ColourMapTexture``. A matrix which transforms values from from this
        data range into texture coordinates is available via the
        :meth:`getCoordinateTransform` method.
        """
        self.set(displayRange=drange)


    def setBorder(self, border):
        """Set the texture border colour. If ``None``, the edge colours of the
        colour map are used as the border.
        """
        self.set(border=border)


    def getCoordinateTransform(self):
        """Returns a matrix which transforms values from from the colour map
        data range (see :meth:`setDisplayRange`) into texture coordinates.
        """
        return self.__coordXform


    def set(self, **kwargs):
        """Set any parameters on this ``ColourMapTexture``. Valid keyword
        arguments are:

        ================ ============================
        ``cmap``         See :meth:`setColourMap`.
        ``invert``       See :meth:`setInvert`.
        ``interp``       See :meth:`setInterp`.
        ``alpha``        See :meth:`setAlpha`.
        ``resolution``   See :meth:`setResolution`.
        ``gamma``        See :meth:`setGamma`.
        ``displayRange`` See :meth:`setDisplayRange`.
        ``border``       See :meth:`setBorder`.
        ================ ============================
        """

        # None is a valid value for any attributes,
        # so we are using 'self' to test whether
        # or not an attribute value was passed in
        cmap         = kwargs.get('cmap',         self)
        invert       = kwargs.get('invert',       self)
        interp       = kwargs.get('interp',       self)
        alpha        = kwargs.get('alpha',        self)
        resolution   = kwargs.get('resolution',   self)
        gamma        = kwargs.get('gamma',        self)
        displayRange = kwargs.get('displayRange', self)
        border       = kwargs.get('border',       self)

        if cmap         is not self: self.__cmap         = cmap
        if invert       is not self: self.__invert       = invert
        if interp       is not self: self.__interp       = interp
        if alpha        is not self: self.__alpha        = alpha
        if displayRange is not self: self.__displayRange = displayRange
        if border       is not self: self.__border       = border
        if resolution   is not self: self.__resolution   = resolution
        if gamma        is not self: self.__gamma        = gamma

        self.__refresh()


    def __prepareTextureSettings(self):
        """Called by :meth:`__refresh`. Prepares all of the texture settings,
        and returns a tuple containing:

          - An array containing the colour map data
          - The display range
          - The interpolation setting
          - The border colour
        """

        import matplotlib.colors as colors

        alpha  = self.__alpha
        cmap   = self.__cmap
        drange = self.__displayRange
        invert = self.__invert
        interp = self.__interp
        res    = self.__resolution
        gamma  = self.__gamma
        border = self.__border

        if drange is None: drange = [0.0, 1.0]
        if invert is None: invert = False
        if interp is None: interp = gl.GL_NEAREST
        if cmap   is None: cmap   = np.zeros((4, 4), dtype=np.float32)
        if res    is None: res    = 256
        if gamma  is None: gamma  = 1

        # The fsleyes.colourmaps module creates
        # ListedColormap instances. If the given
        # cmap is one of these, there's no point
        # in using a resolution greater than the
        # number of colours in the cmap.
        if isinstance(cmap, colors.ListedColormap):
            res = min(res, cmap.colors.shape[0])

        # If cmap is a function, assume that it accepts
        # one or more scalar values between 0 and 1,
        # and converts said values into a numpy array
        # containing RGB/RGBA colours.  Crop the RGB
        # colours, as global alpha takes precedence
        if isinstance(cmap, abc.Callable):

            # Apply gamma scaling to weight
            # towards one end of the colour map
            idxs = np.linspace(0.0, 1.0, res) ** gamma
            cmap = cmap(idxs)
            cmap = cmap[:, :3]

        # If RGB, turn into RGBA. If an RGBA cmap
        # has been provided, their alpha values take
        # precedence over the global alpha setting
        if cmap.shape[1] == 3:
            newCmap        = np.ones((cmap.shape[0], 4), dtype=np.float32)
            newCmap[:, :3] = cmap
            cmap           = newCmap

            # Apply the global alpha if provided
            if alpha is not None:
                cmap[:, 3] = alpha

        # Reverse the colours if necessray
        if invert:
            cmap = cmap[::-1, :]

        # If border is provided and is
        # RGB, convert it to RGBA
        if border is not None and len(border) == 3:
            newBorder     = np.ones(4, dtype=np.float32)
            newBorder[:3] = border
            if alpha is not None:
                newBorder[3] = alpha

            border = newBorder

        return cmap, drange, interp, border


    def __refresh(self):
        """Called when any settings of this ``ColourMapTexture`` are changed.
        Re-configures the texture.
        """

        cmap, drange, interp, border = self.__prepareTextureSettings()

        imin, imax = drange

        # This transformation is used to transform input values
        # from their native range to the range [0.0, 1.0], which
        # is required for texture colour lookup. Values below
        # or above the current display range will be mapped
        # to texture coordinate values less than 0.0 or greater
        # than 1.0 respectively.
        if imax == imin: scale = 0.000000000001
        else:            scale = imax - imin

        coordXform = np.identity(4, dtype=np.float64)
        coordXform[0, 0] = 1.0 / scale
        coordXform[0, 3] = -imin * coordXform[0, 0]

        self.__coordXform = coordXform

        # The colour data is stored on
        # the GPU as 8 bit rgba tuples
        cmap = np.floor(cmap * 255)
        cmap = np.array(cmap, dtype=np.uint8)
        cmap = cmap.ravel(order='C')

        # GL texture creation stuff
        self.bindTexture()

        if border is not None:

            gl.glTexParameterfv(gl.GL_TEXTURE_1D,
                                gl.GL_TEXTURE_BORDER_COLOR,
                                border)
            gl.glTexParameteri( gl.GL_TEXTURE_1D,
                                gl.GL_TEXTURE_WRAP_S,
                                gl.GL_CLAMP_TO_BORDER)
        else:
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)

        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           interp)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           interp)

        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        len(cmap) / 4,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        cmap)
        self.unbindTexture()
