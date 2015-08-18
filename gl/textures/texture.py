#!/usr/bin/env python
#
# texture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.utils.transform as transform


log = logging.getLogger(__name__)


class Texture(object):
    """All subclasses must accept a ``name`` as the first parameter to their
    ``__init__`` method, and must pass said ``name`` through to this
    ``__init__`` method.
    """

    def __init__(self, name, ndims):

        self.__texture     = gl.glGenTextures(1)
        self.__name        = name
        self.__ndims       = ndims
        
        self.__textureUnit = None

        if   ndims == 1: self.__ttype = gl.GL_TEXTURE_1D
        elif ndims == 2: self.__ttype = gl.GL_TEXTURE_2D
        elif ndims == 3: self.__ttype = gl.GL_TEXTURE_3D
        
        else:            raise ValueError('Invalid number of dimensions')

        log.debug('Created {} ({}) for {}: {}'.format(type(self).__name__,
                                                      id(self),
                                                      self.__name,
                                                      self.__texture))

    def getTextureName(self):
        return self.__name

        
    def getTextureHandle(self):
        return self.__texture


    def destroy(self):

        log.debug('Deleting {} ({}) for {}: {}'.format(type(self).__name__,
                                                       id(self),
                                                       self.__name,
                                                       self.__texture))
 
        gl.glDeleteTextures(self.__texture)
        self.__texture = None


    def bindTexture(self, textureUnit=None):

        if textureUnit is not None:
            gl.glActiveTexture(textureUnit)
            gl.glEnable(self.__ttype)

        gl.glBindTexture(self.__ttype, self.__texture)

        self.__textureUnit = textureUnit


    def unbindTexture(self):

        if self.__textureUnit is not None:
            gl.glActiveTexture(self.__textureUnit)
            gl.glDisable(self.__ttype)
            
        gl.glBindTexture(self.__ttype, 0)

        self.__textureUnit = None


class Texture2D(Texture):

    def __init__(self, name, interp=gl.GL_NEAREST):
        Texture.__init__(self, name, 2)

        self.__data      = None
        self.__width     = None
        self.__height    = None
        self.__oldWidth  = None
        self.__oldHeight = None 
        self.__interp    = interp

        
    def setInterpolation(self, interp):
        self.__interp = interp
        self.refresh()


    def setSize(self, width, height):
        """
        Sets the width/height for this texture.

        This method also clears the data for this texture, if it has been
        previously set via the :meth:`setData` method.
        """

        if any((width <= 0, height <= 0)):
            raise ValueError('Invalid size: {}'.format((width, height)))

        self.__setSize(width, height)
        self.__data = None
        
        self.refresh()
        

    def __setSize(self, width, height):
        """Sets the width/height attributes for this texture, and saves a
        reference to the old width/height - see comments in the refresh
        method.
        """
        self.__oldWidth  = self.__width
        self.__oldHeight = self.__height
        self.__width     = width
        self.__height    = height        


    def getSize(self):
        """
        """
        return self.__width, self.__height


    def setData(self, data):
        """
        Sets the data for this texture - the width and height are determined
        from data shape (which is assumed to be 4*width*height).
        """

        self.__setSize(data.shape[1], data.shape[2])
        self.__data = data

        self.refresh()

        
    def refresh(self):

        if any((self.__width  is None,
                self.__height is None,
                self.__width  <= 0,
                self.__height <= 0)):
            raise ValueError('Invalid size: {}'.format((self.__width,
                                                        self.__height)))

        self.bindTexture()
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           self.__interp)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           self.__interp)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)

        data = self.__data

        if data is not None:
            data = data.ravel('F')

        log.debug('Configuring {} ({}) with size {}x{}'.format(
            type(self).__name__,
            self.getTextureHandle(),
            self.__width,
            self.__height))

        # If the width and height have not changed,
        # then we don't need to re-define the texture.
        if self.__width  == self.__oldWidth  and \
           self.__height == self.__oldHeight:

            # But we can use glTexSubImage2D 
            # if we have data to upload
            if data is not None:
                gl.glTexSubImage2D(gl.GL_TEXTURE_2D,
                                   0, 
                                   0,
                                   0,
                                   self.__width,
                                   self.__height,
                                   gl.GL_RGBA,
                                   gl.GL_UNSIGNED_BYTE,
                                   data)
                
        # If the width and/or height have
        # changed, we need to re-define
        # the texture properties
        else:
            gl.glTexImage2D(gl.GL_TEXTURE_2D,
                            0,
                            gl.GL_RGBA8,
                            self.__width,
                            self.__height,
                            0,
                            gl.GL_RGBA,
                            gl.GL_UNSIGNED_BYTE,
                            data)
        self.unbindTexture()

        
    def draw(self, vertices, xform=None):
        
        if vertices.shape != (6, 3):
            raise ValueError('Six vertices must be provided')

        if xform is not None:
            vertices = transform.transform(vertices, xform)

        vertices  = np.array(vertices, dtype=np.float32)
        texCoords = np.zeros((6, 2),   dtype=np.float32)
        indices   = np.arange(6,       dtype=np.uint32)

        texCoords[0, :] = [0, 0]
        texCoords[1, :] = [0, 1]
        texCoords[2, :] = [1, 0]
        texCoords[3, :] = [1, 0]
        texCoords[4, :] = [0, 1]
        texCoords[5, :] = [1, 1]

        vertices  = vertices .ravel('C')
        texCoords = texCoords.ravel('C')

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        self.bindTexture(gl.GL_TEXTURE0)

        gl.glClientActiveTexture(gl.GL_TEXTURE0)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

        gl.glTexEnvf(gl.GL_TEXTURE_ENV,
                     gl.GL_TEXTURE_ENV_MODE,
                     gl.GL_REPLACE)

        gl.glVertexPointer(  3, gl.GL_FLOAT, 0, vertices)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, texCoords)

        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, indices) 

        self.unbindTexture()

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY) 
 
        
    def drawOnBounds(self, zpos, xmin, xmax, ymin, ymax, xax, yax, xform=None):

        zax              = 3 - xax - yax
        vertices         = np.zeros((6, 3), dtype=np.float32)
        vertices[:, zax] = zpos

        vertices[ 0, [xax, yax]] = [xmin, ymin]
        vertices[ 1, [xax, yax]] = [xmin, ymax]
        vertices[ 2, [xax, yax]] = [xmax, ymin]
        vertices[ 3, [xax, yax]] = [xmax, ymin]
        vertices[ 4, [xax, yax]] = [xmin, ymax]
        vertices[ 5, [xax, yax]] = [xmax, ymax]

        self.draw(vertices, xform)
