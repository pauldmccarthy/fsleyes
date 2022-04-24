#!/usr/bin/env python
#
# texture2d.py - The Texture2D class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Texture2D` and :class:`DepthTexture`
classes.
"""


import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.transform.affine        as affine
import fsl.data.utils              as dutils
import fsleyes.gl                  as fslgl
import fsleyes.gl.shaders          as shaders
import fsleyes.gl.textures.texture as texture


log = logging.getLogger(__name__)


class DepthTexture(texture.Texture):
    """The ``DepthTexture`` class is a 2D ``GL_DEPTH_COMPONENT24`` texture
    which is used by the :class:`.RenderTexture` class.

    A ``DepthTexture`` is configured by setting its :meth:`.Texture.shape`
    property to the desired width/height.
    """


    def __init__(self, name):
        """Create a ``DepthTexture``

        :arg name: Unique name for this texture
        """
        texture.Texture.__init__(self, name, 2, 1, dtype=np.uint32)


    @property
    def dtype(self):
        """Overrides :meth:`.Texture.dtype`. """
        return np.uint32


    @dtype.setter
    def dtype(self):
        """Overrides the :meth:`.Texture.dtype` setter. Raises
        ``NotImplementedError``.
        """
        raise NotImplementedError()


    @property
    def textureType(self):
        """Overrides :meth:`.Texture.textureType`. """
        return gl.GL_UNSIGNED_INT


    @property
    def baseFormat(self):
        """Overrides :meth:`.Texture.baseFormat`. """
        return gl.GL_DEPTH_COMPONENT

    @property
    def internalFormat(self):
        """Overrides :meth:`.Texture.internalFormat`. """
        return gl.GL_DEPTH_COMPONENT24


    @texture.Texture.data.setter
    def data(self, data):
        """Overrides the :meth:`.Texture.data` setter. Raises an error -
        you cannot set data on a ``DepthTexture``.
        """
        raise NotImplementedError('Cannot set data on a DepthTexture')


    def doRefresh(self):
        """Refreshes this ``DepthTexture`` based on the current
        :meth:`.Texture.shape`.
        """

        width, height = self.shape
        ttype         = self.textureType
        intFmt        = self.internalFormat
        baseFmt       = self.baseFormat

        with self.bound():

            gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_COMPARE_MODE,
                               gl.GL_NONE)

            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_MAG_FILTER,
                               gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_MIN_FILTER,
                               gl.GL_NEAREST)

            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_T,
                               gl.GL_CLAMP_TO_EDGE)
            gl.glTexImage2D(gl.GL_TEXTURE_2D,
                            0,
                            intFmt,
                            width,
                            height,
                            0,
                            baseFmt,
                            ttype,
                            None)


    def getBitmap(self):
        """Returns the data stored in this ``DepthTexture`` as a ``numpy.uint8``
        array of shape ``(height, width, 3)``.

        The depth values are inverted and normalised, and duplicated across
        the three RGB channels.
        """

        intFmt        = self.baseFormat
        extFmt        = self.textureType
        ndtype        = self.dtype
        width, height = self.shape

        with self.bound():
            data = gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, intFmt, extFmt, None)

        data = np.frombuffer(data, dtype=ndtype).astype(np.float32)
        data = (data.max() - data)
        data = (data - data.min()) / (data.max() - data.min())
        data = (data * 255).astype(np.uint8)

        data = data.reshape((height, width, 1))
        data = np.dstack((data, data, data))
        data = np.flipud(data)

        return data


class Texture2D(texture.Texture):
    """The ``Texture2D`` class represents a 2D texture. A ``Texture2D``
    instance can be used in one of two ways:

      - Setting the texture data via the :meth:`.Texture.data` method, and then
        drawing it to a scene via :meth:`draw` or :meth:`drawOnBounds`.

      - Setting the texture size via :meth:`.Texture.shape`, and then drawing
        to it by some other means (see e.g. the :class:`.RenderTexture` class,
        a sub-class of ``Texture2D``).
    """


    def __init__(self, name, **kwargs):
        """Create a ``Texture2D`` instance.

        :arg name: Unique name for this ``Texture2D``.
        """

        nvals = kwargs.pop('nvals', 4)

        if nvals not in (1, 3, 4):
            raise ValueError('nvals must be 1, 3 or 4')

        # We keep a copy of the current
        # width/height, so we can detect
        # whether it has changed, and
        # skip unnecessary processing
        self.__width  = None
        self.__height = None

        # If this texture is drawn via
        # the draw method, a shader
        # program is compiled and used.
        # The __shader method compiles
        # it and stores it here.
        self.__defaultShader = None

        texture.Texture.__init__(self, name, 2, nvals, **kwargs)


    def destroy(self):
        """Must be called when this ``Texture2D`` is no longer needed. """
        super().destroy()
        if self.__defaultShader is not None:
            self.__defaultShader.destroy()
            self.__defaultShader = None


    def doRefresh(self):
        """Overrides :meth:`.Texture.doRefresh`. Configures this ``Texture2D``.
        This includes setting up interpolation, and setting the texture size
        and data.
        """

        data = self.preparedData

        if   data is None:    width, height = self.shape
        elif self.nvals == 1: width, height = data.shape
        else:                 width, height = data.shape[1:]

        if data is not None:
            data = np.array(data.ravel('F'), copy=False)
            data = dutils.makeWriteable(data)

        interp = self.interp

        if interp is None:
            interp = gl.GL_NEAREST

        with self.bound():

            gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_MAG_FILTER,
                               interp)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_MIN_FILTER,
                               interp)

            if self.border is not None:
                gl.glTexParameteri(gl.GL_TEXTURE_2D,
                                   gl.GL_TEXTURE_WRAP_S,
                                   gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_2D,
                                   gl.GL_TEXTURE_WRAP_T,
                                   gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameterfv(gl.GL_TEXTURE_2D,
                                    gl.GL_TEXTURE_BORDER_COLOR,
                                    np.asarray(self.border, dtype=np.float32))
            else:
                gl.glTexParameteri(gl.GL_TEXTURE_2D,
                                   gl.GL_TEXTURE_WRAP_S,
                                   gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_2D,
                                   gl.GL_TEXTURE_WRAP_T,
                                   gl.GL_CLAMP_TO_EDGE)

            # If the width and height have not
            # changed, then we don't need to
            # re-define the texture. But we can
            # use glTexSubImage2D if we have
            # data to upload
            if width  == self.__width  and \
               height == self.__height and \
               data is not None:
                gl.glTexSubImage2D(gl.GL_TEXTURE_2D,
                                   0,
                                   0,
                                   0,
                                   width,
                                   height,
                                   self.baseFormat,
                                   self.textureType,
                                   data)

            # If the width and/or height have
            # changed, we need to re-define
            # the texture properties
            else:
                self.__width  = width
                self.__height = height
                gl.glTexImage2D(gl.GL_TEXTURE_2D,
                                0,
                                self.internalFormat,
                                width,
                                height,
                                0,
                                self.baseFormat,
                                self.textureType,
                                data)


    def shapeData(self, data, oldShape=None):
        """Overrides :meth:`.Texture.shapeData`.

        This method is used by ``Texture2D`` sub-classes which are used to
        store 3D image data (e.g. the :class:`.ImageTexture2D` class). It
        shapes the data, ensuring that it is compatible with a 2D texture.

        :arg data:     ``numpy`` array containing the data
        :arg oldShape: Original data shape; if not provided, is taken from
                       ``data``.
        """

        nvals = self.nvals

        # For scalar, 1D or 2D data, we need
        # to make sure the data has a shape
        # compatible with the Texture2D
        if oldShape is None:
            oldShape = data.shape

        if nvals == 1:
            datShape = data.shape
        else:
            oldShape = oldShape[1:]
            datShape = data.shape[1:]

        oldShape = np.array(oldShape)
        datShape = np.array(datShape)

        if   np.all(oldShape         == [1, 1, 1]): newShape = ( 1,  1)
        elif np.all(oldShape[1:]     == [1, 1]):    newShape = (-1,  1)
        elif np.all(oldShape[[0, 2]] == [1, 1]):    newShape = (-1,  1)
        elif np.all(oldShape[:2]     == [1, 1]):    newShape = ( 1, -1)
        elif        oldShape[2]      == 1:          newShape = datShape[:2]
        elif        oldShape[1]      == 1:          newShape = datShape[[0, 2]]
        elif        oldShape[0]      == 1:          newShape = datShape[1:]

        if nvals > 1:
            newShape = [nvals] + list(newShape)

        return data.reshape(newShape)


    def texCoordXform(self, origShape):
        """Overrides :meth:`.Texture.texCoordXform`.

        Returns an affine matrix which encodes a rotation that maps the two
        major axes of the image voxel coordinate system to the first two axes
        of the texture coordinate system.

        This method is used by sub-classes which are being used to store 3D
        image data, e.g. the :class:`.ImageTexture2D` and
        :class:`.SelectionTexture2D` classes.

        If this texture does not have any data yet, this method will return
        ``None``.
        """

        scales  = [1, 1, 1]
        offsets = [0, 0, 0]
        rots    = [0, 0, 0]

        if origShape is None:
            return None

        # Here we apply a rotation to the
        # coordinates to force the two major
        # voxel axes to map to the first two
        # texture coordinate axes
        if origShape[0] == 1:
            rots      = [0, -np.pi / 2, -np.pi / 2]
        elif origShape[1] == 1:
            rots      = [-np.pi / 2, 0, 0]
            scales[1] = -1

        return affine.compose(scales, offsets, rots)


    def doPatch(self, data, offset):
        """Overrides :meth:`.Texture.doPatch`. Updates part of the texture
        data.
        """
        shape = data.shape
        data  = data.flatten(order='F')

        with self.bound():
            gl.glTexSubImage2D(gl.GL_TEXTURE_2D,
                               0,
                               offset[0],
                               offset[1],
                               shape[0],
                               shape[1],
                               self.baseFormat,
                               self.textureType,
                               data)


    def __shader(self):
        """Returns a shader program to draw the contents of this ``Texture2D``.
        Used by :meth:`draw`.
        """
        if self.__defaultShader is None:
            vertSrc   = shaders.getVertexShader(  'texture2d')
            fragSrc   = shaders.getFragmentShader('texture2d')

            if float(fslgl.GL_COMPATIBILITY) < 2.1:
                shader = shaders.ARBPShader(vertSrc, fragSrc, {'texture' : 0})
            else:
                shader = shaders.GLSLShader(vertSrc, fragSrc)
                with shader.loaded():
                    shader.set('tex', 0)
            self.__defaultShader = shader
        return self.__defaultShader


    def draw(self, vertices):
        """Draw the contents of this ``Texture2D`` to a region specified by
        the given vertices.
        """

        shader    = self.__shader()
        vertices  = np.array(vertices, dtype=np.float32)
        nverts    = vertices.shape[0]
        texCoords = self.generateTextureCoords()

        with self.bound(gl.GL_TEXTURE0), shader.loaded():
            shader.setAtt('vertex',   vertices)
            shader.setAtt('texCoord', texCoords)
            shader.draw(gl.GL_TRIANGLES, 0, nverts)


    def drawOnBounds(self,
                     zpos,
                     xmin,
                     xmax,
                     ymin,
                     ymax,
                     xax,
                     yax,
                     xform=None):
        """Draws the contents of this ``Texture2D`` to a rectangle.  This is a
        convenience method which creates a set of vertices, and passes them to
        the :meth:`draw` method.

        :arg zpos:  Position along the Z axis, in the display coordinate
                    system.
        :arg xmin:  Minimum X axis coordinate.
        :arg xmax:  Maximum X axis coordinate.
        :arg ymin:  Minimum Y axis coordinate.
        :arg ymax:  Maximum Y axis coordinate.
        :arg xax:   Display space axis which maps to the horizontal screen
                    axis.
        :arg yax:   Display space axis which maps to the vertical screen
                    axis.
        :arg xform: Transformation matrix to apply to the vertices.

        All other arguments are passed to the :meth:`draw` method.
        """

        vertices = self.generateVertices(
            zpos, xmin, xmax, ymin, ymax, xax, yax)
        if xform is not None:
            vertices = affine.transform(vertices, xform)
        self.draw(vertices)


    @classmethod
    def generateVertices(cls, zpos, xmin, xmax, ymin, ymax, xax, yax):
        """Generates a set of vertices suitable for passing to the
        :meth:`.Texture2D.draw` method, for drawing a ``Texture2D`` to a 2D
        canvas, with the ``GL_TRIANGLES`` primitive.

        :arg zpos:  Position along the Z axis, in the display coordinate
                    system.
        :arg xmin:  Minimum X axis coordinate.
        :arg xmax:  Maximum X axis coordinate.
        :arg ymin:  Minimum Y axis coordinate.
        :arg ymax:  Maximum Y axis coordinate.
        :arg xax:   Display space axis which maps to the horizontal screen
                    axis.
        :arg yax:   Display space axis which maps to the vertical screen
                    axis.
        """

        zax              = 3 - xax - yax
        vertices         = np.zeros((6, 3), dtype=np.float32)
        vertices[:, zax] = zpos

        vertices[ 0, [xax, yax]] = [xmin, ymin]
        vertices[ 1, [xax, yax]] = [xmin, ymax]
        vertices[ 2, [xax, yax]] = [xmax, ymin]
        vertices[ 3, [xax, yax]] = [xmax, ymin]
        vertices[ 4, [xax, yax]] = [xmin, ymax]
        vertices[ 5, [xax, yax]] = [xmax, ymax]

        return vertices


    @classmethod
    def generateTextureCoords(cls):
        """Generates a set of texture coordinates for drawing a
        :class:`Texture2D`. This function is used by the
        :meth:`Texture2D.draw` method.
        """

        texCoords       = np.zeros((6, 2), dtype=np.float32)
        texCoords[0, :] = [0, 0]
        texCoords[1, :] = [0, 1]
        texCoords[2, :] = [1, 0]
        texCoords[3, :] = [1, 0]
        texCoords[4, :] = [0, 1]
        texCoords[5, :] = [1, 1]

        return texCoords


    def getBitmap(self):
        """Returns the data stored in this ``Texture2D`` as a ``numpy.uint8``
        array of shape ``(height, width, 4)``.
        """

        intFmt        = self.baseFormat
        extFmt        = self.textureType
        ndtype        = self.dtype
        nvals         = self.nvals
        width, height = self.shape

        with self.bound():
            data = gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, intFmt, extFmt, None)

        data = np.frombuffer(data, dtype=ndtype)
        data = data.reshape((height, width, nvals))
        data = np.flipud(data)

        return data
