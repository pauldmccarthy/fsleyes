#!/usr/bin/env python
#
# colourmaptexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
import collections


import numpy     as np
import OpenGL.GL as gl

import texture


log = logging.getLogger(__name__)


class ColourMapTexture(texture.Texture):


    def __init__(self, name):
        
        texture.Texture.__init__(self, name, 1)
        
        self.__resolution   = None
        self.__cmap         = None
        self.__invert       = False
        self.__interp       = None
        self.__alpha        = None
        self.__displayRange = None
        self.__border       = None
        self.__coordXform   = None


    # CMAP can be either a function which transforms
    # values to RGBA, or a N*4 numpy array containing
    # RGBA values
    def setColourMap(   self, cmap):   self.set(cmap=cmap)
    def setResolution(  self, res):    self.set(resolution=res)
    def setAlpha(       self, alpha):  self.set(alpha=alpha)
    def setInvert(      self, invert): self.set(invert=invert)
    def setInterp(      self, interp): self.set(interp=interp)
    def setDisplayRange(self, drange): self.set(displayRange=drange)
    def setBorder(      self, border): self.set(border=border)


    def getCoordinateTransform(self):
        return self.__coordXform

    
    def set(self, **kwargs):

        # None is a valid value for any attributes,
        # so we are using 'self' to test whether
        # or not an attribute value was passed in
        cmap         = kwargs.get('cmap',         self)
        invert       = kwargs.get('invert',       self)
        interp       = kwargs.get('interp',       self)
        alpha        = kwargs.get('alpha',        self)
        resolution   = kwargs.get('resolution',   self)
        displayRange = kwargs.get('displayRange', self)
        border       = kwargs.get('border',       self)

        if cmap         is not self: self.__cmap         = cmap
        if invert       is not self: self.__invert       = invert
        if interp       is not self: self.__interp       = interp
        if alpha        is not self: self.__alpha        = alpha
        if displayRange is not self: self.__displayRange = displayRange
        if border       is not self: self.__border       = border
        if resolution   is not self: self.__resolution   = resolution

        self.__refresh()


    def __prepareTextureSettings(self):

        alpha  = self.__alpha
        cmap   = self.__cmap
        drange = self.__displayRange
        invert = self.__invert
        interp = self.__interp
        res    = self.__resolution
        border = self.__border

        if drange is None: drange = [0.0, 1.0]
        if invert is None: invert = False
        if interp is None: interp = gl.GL_NEAREST
        if cmap   is None: cmap   = np.zeros((4, 4), dtype=np.float32)
        if res    is None: res    = 256

        # If cmap is a function, assume that it accepts
        # one or more scalar values between 0 and 1,
        # and converts said values into a numpy array
        # containing RGB/RGBA colours.  Crop the RGB
        # colours, as global alpha takes precedence
        if isinstance(cmap, collections.Callable):
            cmap = cmap(np.linspace(0.0, 1.0, res))
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
        
        coordXform = np.identity(4, dtype=np.float32)
        coordXform[0, 0] = 1.0 / scale
        coordXform[3, 0] = -imin * coordXform[0, 0]

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
