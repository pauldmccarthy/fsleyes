#!/usr/bin/env python
#
# lookuptabletexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL as gl
import numpy     as np


import texture
import fsl.fsleyes.colourmaps as fslcmaps


log = logging.getLogger(__name__)


class LookupTableTexture(texture.Texture):

    def __init__(self, name):
        
        texture.Texture.__init__(self, name, 1)
        
        self.__lut        = None
        self.__alpha      = None
        self.__brightness = None
        self.__contrast   = None


    def set(self, **kwargs):

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
        self.__refresh()

        
    def __refresh(self, *a):

        lut        = self.__lut
        alpha      = self.__alpha
        brightness = self.__brightness
        contrast   = self.__contrast

        if lut is None:
            raise RuntimeError('Lookup table has not been defined')

        if brightness is None: brightness = 0.5 
        if contrast   is None: contrast   = 0.5

        # Enough memory is allocated for the lut texture
        # so that shader programs can use label values
        # as indices into the texture. Not very memory
        # efficient, but greatly reduces complexity.
        nvals  = lut.max() + 1
        data   = np.zeros((nvals, 4), dtype=np.uint8)

        for lbl in lut.labels:

            value  = lbl.value()
            colour = fslcmaps.applyBricon(lbl.colour(), brightness, contrast)

            data[value, :3] = [np.floor(c * 255) for c in colour]

            if not lbl.enabled():   data[value, 3] = 0
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
