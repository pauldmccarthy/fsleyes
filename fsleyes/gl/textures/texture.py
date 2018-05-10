#!/usr/bin/env python
#
# texture.py - The Texture and Texture2D classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Texture` and :class:`Texture2D` classes,
which are the base classes for all other texture types. See also the
:class:`.Texture3D` class.
"""


import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.utils.transform as transform
import fsleyes.gl.routines as glroutines


log = logging.getLogger(__name__)


class Texture(object):
    """The ``Texture`` class is the base class for all other texture types in
    *FSLeyes*. This class is not intended to be used directly - use one of the
    sub-classes instead. This class provides a few convenience methods for
    working with textures:

    .. autosummary::
       :nosignatures:

       getTextureName
       getTextureHandle


    The :meth:`bindTexture` and :meth:`unbindTexture` methods allow you to
    bind a texture object to a GL texture unit. For example, let's say we
    have a texture object called ``tex``, and we want to use it::

        import OpenGL.GL as gl


        # Bind the texture before doing any configuration -
        # we don't need to specify a texture unit here.
        tex.bindTexture()

        # Use nearest neighbour interpolation
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)

        tex.unbindTexture()

        # ...

        # When we want to use the texture in a
        # scene render, we need to bind it to
        # a texture unit.
        tex.bindTexture(gl.GL_TEXTURE0)

        # ...
        # Do the render
        # ...

        tex.unbindTexture()


    .. note:: Despite what is shown in the example above, you shouldn't need
              to manually configure texture objects with calls to
              ``glTexParameter`` - most things can be performed through
              methods of the ``Texture`` sub-classes, for example
              :class:`.ImageTexture` and :class:`.Texture2D`.


    See the :mod:`.resources` module for a method of sharing texture
    resources.
    """


    def __init__(self, name, ndims):
        """Create a ``Texture``.

        :arg name:  The name of this texture - should be unique.
        :arg ndims: Number of dimensions - must be 1, 2 or 3.

        .. note:: All subclasses must accept a ``name`` as the first parameter
                  to their ``__init__`` method, and must pass said ``name``
                  through to the :meth:`__init__` method.
        """

        self.__texture     = int(gl.glGenTextures(1))
        self.__name        = name
        self.__ndims       = ndims
        self.__bound       = False

        self.__textureUnit = None

        if   ndims == 1: self.__ttype = gl.GL_TEXTURE_1D
        elif ndims == 2: self.__ttype = gl.GL_TEXTURE_2D
        elif ndims == 3: self.__ttype = gl.GL_TEXTURE_3D

        else:            raise ValueError('Invalid number of dimensions')

        log.debug('{}.init ({})'.format(type(self).__name__, id(self)))
        log.debug('Created {} ({}) for {}: {}'.format(type(self).__name__,
                                                      id(self),
                                                      self.__name,
                                                      self.__texture))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.debug('{}.del ({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """Must be called when this ``Texture`` is no longer needed. Deletes
        the texture handle.
        """

        log.debug('Deleting {} ({}) for {}: {}'.format(type(self).__name__,
                                                       id(self),
                                                       self.__name,
                                                       self.__texture))

        gl.glDeleteTextures(self.__texture)
        self.__texture = None


    def getTextureName(self):
        """Returns the name of this texture. This is not the GL texture name,
        rather it is the unique name passed into :meth:`__init__`.
        """
        return self.__name


    def getTextureHandle(self):
        """Returns the GL texture handle for this texture. """
        return self.__texture


    def isBound(self):
        """Returns ``True`` if this texture is currently bound, ``False``
        otherwise.

        .. note:: This method assumes that the :meth:`bindTexture` and
                 :meth:`unbindTexture` methods are called in pairs.
        """
        return self.__bound


    def bindTexture(self, textureUnit=None):
        """Activates and binds this texture.

        :arg textureUnit: The texture unit to bind this texture to, e.g.
                          ``GL_TEXTURE0``.
        """

        if textureUnit is not None:
            gl.glActiveTexture(textureUnit)

        gl.glBindTexture(self.__ttype, self.__texture)

        self.__bound       = True
        self.__textureUnit = textureUnit


    def unbindTexture(self):
        """Unbinds this texture. """

        if self.__textureUnit is not None:
            gl.glActiveTexture(self.__textureUnit)

        gl.glBindTexture(self.__ttype, 0)

        self.__bound       = False
        self.__textureUnit = None


class Texture2D(Texture):
    """The ``Texture2D`` class represents a two-dimensional RGBA texture. A
    ``Texture2D`` instance can be used in one of two ways:

      - Setting the texture data via the :meth:`setData` method, and then
        drawing it to a scene via :meth:`draw` or :meth:`drawOnBounds`.

      - Setting the texture size via :meth:`setSize`, and then drawing to it
        by some other means (see e.g. the :class:`.RenderTexture` class, a
        sub-class of ``Texture2D``).
    """

    def __init__(self, name, interp=gl.GL_NEAREST, dtype=None):
        """Create a ``Texture2D`` instance.

        :arg name:   Unique name for this ``Texture2D``.

        :arg interp: Initial interpolation - ``GL_NEAREST`` (the default)
                     or ``GL_LINEAR``. This can be changed later on via the
                     :meth:`setInterpolation` method.

        :arg dtype:  Sized internal GL data format to use for the texture.
                     Currently only ``gl.GL_RGBA8`` (the default) and
                     ``gl.GL_DEPTH_COMPONENT24`` are supported.
        """

        if dtype is None:
            dtype = gl.GL_RGBA8

        if dtype not in (gl.GL_RGBA8, gl.GL_DEPTH_COMPONENT24):
            raise ValueError('Invalid dtype: {}'.format(dtype))

        Texture.__init__(self, name, 2)

        self.__data      = None
        self.__width     = None
        self.__height    = None
        self.__oldWidth  = None
        self.__oldHeight = None
        self.__border    = None
        self.__interp    = interp
        self.__dtype     = dtype


    def setInterpolation(self, interp):
        """Change the texture interpolation - valid values are ``GL_NEAREST``
        or ``GL_LINEAR``.
        """
        self.__interp = interp
        self.refresh()


    def setBorder(self, border):
        """Change the border colour - set to a tuple of four values in the
        range 0 to 1, or ``None`` for no border (in which case the texture
        coordinates will be clamped to edges).
        """
        self.__border = border
        self.refresh()


    def setSize(self, width, height):
        """Sets the width/height for this texture.

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


    @classmethod
    def getDataTypeParams(cls, dtype):
        """Returns a tuple containing information about the given sized
        internal GL texture data format:
        - The base GL internal format
        - The GL external data format
        - The equivalent ``numpy`` data type
        - The number of channels
        """

        if dtype == gl.GL_RGBA8:
            intFmt = gl.GL_RGBA
            extFmt = gl.GL_UNSIGNED_BYTE
            ndtype = np.uint8
            size   = 4

        elif dtype == gl.GL_DEPTH_COMPONENT24:
            intFmt = gl.GL_DEPTH_COMPONENT
            extFmt = gl.GL_UNSIGNED_INT
            ndtype = np.uint32
            size   = 1

        return intFmt, extFmt, ndtype, size


    @property
    def dtype(self):
        """Returns the internal GL data format to use for this texture. """

        return self.__dtype


    def getSize(self):
        """Return the current ``(width, height)`` of this ``Texture2D``. """
        return self.__width, self.__height


    def setData(self, data):
        """Sets the data for this texture - the width and height are determined
        from data shape, which is assumed to be 4*width*height.
        """

        self.__setSize(data.shape[1], data.shape[2])
        self.__data = data

        self.refresh()


    def getData(self):
        """Returns the data stored in this ``Texture2D`` as a ``numpy.uint8``
        array of shape ``(height, width, 4)``.
        """

        bound = self.isBound()

        if not bound:
            self.bindTexture()

        intFmt, extFmt, ndtype, size = self.getDataTypeParams(self.__dtype)

        data = gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, intFmt, extFmt, None)

        if not bound:
            self.unbindTexture()

        data = np.frombuffer(data, dtype=ndtype)
        data = data.reshape((self.__height, self.__width, size))
        data = np.flipud(data)

        return data


    def refresh(self):
        """Configures this ``Texture2D``. This includes setting up
        interpolation, and setting the texture size and data.
        """

        if any((self.__width  is None,
                self.__height is None,
                self.__width  <= 0,
                self.__height <= 0)):
            raise ValueError('Invalid size: {}'.format((self.__width,
                                                        self.__height)))

        dtype                  = self.__dtype
        intFmt, extFmt, ndtype = self.getDataTypeParams(dtype)[:3]

        data = self.__data

        if data is not None:
            data = np.array(data.ravel('F'), dtype=ndtype, copy=False)

        self.bindTexture()
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           self.__interp)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           self.__interp)

        if self.__border is not None:
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_T,
                               gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameterfv(gl.GL_TEXTURE_2D,
                                gl.GL_TEXTURE_BORDER_COLOR,
                                self.__border)
        else:
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_T,
                               gl.GL_CLAMP_TO_EDGE)

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
                                   intFmt,
                                   extFmt,
                                   data)

        # If the width and/or height have
        # changed, we need to re-define
        # the texture properties
        else:
            gl.glTexImage2D(gl.GL_TEXTURE_2D,
                            0,
                            dtype,
                            self.__width,
                            self.__height,
                            0,
                            intFmt,
                            extFmt,
                            data)
        self.unbindTexture()


    def __prepareCoords(self, vertices, xform=None):
        """Called by :meth:`draw`. Prepares vertices, texture coordinates and
        indices for drawing the texture.

        If ``vertices is None``, it is assumed that the caller has already
        assigned vertices and texture coordinates, either via a shader, or
        via vertex/texture coordinate pointers. In this case,

        :returns: A tuple containing the vertices, texture coordinates, and
                  indices, or ``(None, None, indices)`` if
                  ``vertices is None``
        """

        indices = np.arange(6, dtype=np.uint32)

        if vertices is None:
            return None, None, indices

        if vertices.shape != (6, 3):
            raise ValueError('Six vertices must be provided')

        if xform is not None:
            vertices = transform.transform(vertices, xform)

        vertices  = np.array(vertices, dtype=np.float32).ravel('C')
        texCoords = self.generateTextureCoords()        .ravel('C')

        return vertices, texCoords, indices


    def draw(self,
             vertices=None,
             xform=None,
             textureUnit=None):
        """Draw the contents of this ``Texture2D`` to a region specified by
        the given vertices. The texture is bound to texture unit 0.

        :arg vertices:    A ``numpy`` array of shape ``6 * 3`` specifying the
                          region, made up of two triangles, to which this
                          ``Texture2D`` should be drawn. If ``None``, it is
                          assumed that the vertices and texture coordinates
                          have already been configured (e.g. via a shader
                          program).

        :arg xform:       A transformation to be applied to the vertices.
                          Ignored if ``vertices is None``.

        :arg textureUnit: Texture unit to bind to. Defaults to
                          ``gl.GL_TEXTURE0``.
        """

        if textureUnit is None:
            textureUnit = gl.GL_TEXTURE0

        vertices, texCoords, indices = self.__prepareCoords(vertices, xform)

        self.bindTexture(textureUnit)
        gl.glClientActiveTexture(textureUnit)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV,
                     gl.GL_TEXTURE_ENV_MODE,
                     gl.GL_REPLACE)


        glfeatures = [gl.GL_TEXTURE_2D, gl.GL_VERTEX_ARRAY]

        # Only enable texture coordinates if we know
        # that there are texture coordinates. Some GL
        # platforms will crash if texcoords are
        # enabled on a texture unit, but no texcoords
        # are loaded.
        if vertices is not None:
            glfeatures.append(gl.GL_TEXTURE_COORD_ARRAY)

        with glroutines.enabled(glfeatures):

            if vertices is not None:
                gl.glVertexPointer(  3, gl.GL_FLOAT, 0, vertices)
                gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, texCoords)

            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, indices)

        self.unbindTexture()


    def drawOnBounds(self,
                     zpos,
                     xmin,
                     xmax,
                     ymin,
                     ymax,
                     xax,
                     yax,
                     *args,
                     **kwargs):
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

        All other arguments are passed to the :meth:`draw` method.
        """

        vertices = self.generateVertices(
            zpos, xmin, xmax, ymin, ymax, xax, yax)
        self.draw(vertices, *args, **kwargs)


    @classmethod
    def generateVertices(
            cls, zpos, xmin, xmax, ymin, ymax, xax, yax, xform=None):
        """Generates a set of vertices suitable for passing to the
        :meth:`.Texture2D.draw` method, for drawing a ``Texture2D`` to a 2D
        canvas.

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
        :arg xform: Transformation matrix to appply to vertices.
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

        if xform is not None:
            vertices = transform.transform(vertices, xform)

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
