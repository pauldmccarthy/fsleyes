#!/usr/bin/env python
#
# texture3d.py - The Texture3D class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Texture3D` class, which represents a
3D OpenGL texture.
"""


import functools as ft
import              logging
import              platform

import numpy as np

import fsl.data.utils          as dutils
import fsleyes.gl              as fslgl
from   fsleyes.gl.textures import texture
from   fsleyes.utils       import lazyimport


log = logging.getLogger(__name__)


gl = lazyimport('OpenGL.GL', f'{__name__}.gl')


class Texture3D(texture.Texture):
    """The ``Texture3D`` class contains the logic required to create and
    manage a 3D texture.
    """

    @staticmethod
    @ft.cache
    def _needRecreate():
        """Returns ``True`` if the texture handle should be recreated
        on every call to :meth:`doRefresh`, ``False`` otherwise.

        For 3D textures of a certain size, and on Intel macs using an
        integrated Intel GPU, the ``glTexImage3D`` function does not seem to
        successfully populate texture data for existing textures. The first
        call succeeds, but then subsequent calls (e.g. to refresh the texture
        for a 4D image when the volume is changed) fail silently, leaving us
        with a corrupted texture and display.

        The only workaround I can come up with is to delete and recreate the
        texture handle every time the texture is refreshed.
        """

        return platform.system() == 'Darwin' and \
            'intel' in fslgl.GL_RENDERER.lower()


    def __init__(self, name, **kwargs):
        """Create a ``Texture3D``.

        :arg name: A unique name for the texture.

        All other keyword arguments are passed through to
        :meth:`.Texture.__init__`.
        """

        kwargs['nvals'] = kwargs.get('nvals', 1)

        if kwargs['nvals'] not in (1, 3, 4):
            raise ValueError('nvals must be either 1, 3 or 4')

        texture.Texture.__init__(self, name, 3, **kwargs)


    def doRefresh(self):
        """Overrides :meth:`.Texture.doRefresh`.

        (Re-)configures the OpenGL texture.
        """

        data = self.preparedData

        if data is None:
            return

        log.debug('Configuring 3D texture (id %s) for %s (data shape: %s)',
                  self.name, self.handle, self.shape)

        # First dimension for multi-
        # valued textures
        if self.nvals > 1: shape = data.shape[1:]
        else:              shape = data.shape

        # The image data is flattened, with
        # fortran dimension ordering, so the
        # data, as stored on the GPU, has its
        # first dimension as the fastest
        # changing.
        data = np.asarray(data.ravel(order='F'))

        # PyOpenGL needs the data array
        # to be writeable, as it uses
        # PyArray_ISCARRAY to check
        # for contiguousness. but if the
        # data has come from a nibabel
        # ArrayProxy, the writeable flag
        # will be set to False for some
        # reason.
        data    = dutils.makeWriteable(data)
        interp  = self.interp
        intFmt  = self.internalFormat
        baseFmt = self.baseFormat
        ttype   = self.textureType

        if interp is None:
            interp = gl.GL_NEAREST

        # Delete and recreate the texture
        # handle on problematic platforms
        if self._needRecreate():
            self.recreateHandle()

        with self.bound():

            # Enable storage of tightly packed data of any size (i.e.
            # our texture shape does not have to be divisible by 4).
            gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

            # Disable mipmapping
            gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_BASE_LEVEL, 0)
            gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_MAX_LEVEL,  0)

            # Interpolation
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_MAG_FILTER,
                               interp)
            gl.glTexParameteri(gl.GL_TEXTURE_3D,
                               gl.GL_TEXTURE_MIN_FILTER,
                               interp)

            # Clamp texture borders to
            # the specified border value(s)
            if self.border is not None:
                gl.glTexParameteri(gl.GL_TEXTURE_3D,
                                   gl.GL_TEXTURE_WRAP_S,
                                   gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_3D,
                                   gl.GL_TEXTURE_WRAP_T,
                                   gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_3D,
                                   gl.GL_TEXTURE_WRAP_R,
                                   gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameterfv(gl.GL_TEXTURE_3D,
                                    gl.GL_TEXTURE_BORDER_COLOR,
                                    np.asarray(self.border, dtype=np.float32))

            # Clamp texture borders to the edge
            # values - it is the responsibility
            # of the rendering logic to not draw
            # anything outside of the image space
            else:
                gl.glTexParameteri(gl.GL_TEXTURE_3D,
                                   gl.GL_TEXTURE_WRAP_S,
                                   gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_3D,
                                   gl.GL_TEXTURE_WRAP_T,
                                   gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_3D,
                                   gl.GL_TEXTURE_WRAP_R,
                                   gl.GL_CLAMP_TO_EDGE)

            # create the texture according to
            # the format determined by the
            # determineTextureType method.
            gl.glTexImage3D(gl.GL_TEXTURE_3D,
                            0,
                            intFmt,
                            shape[0],
                            shape[1],
                            shape[2],
                            0,
                            baseFmt,
                            ttype,
                            data)


    def doPatch(self, data, offset):
        """Overrides :meth:`.Texture.doPatch`. Updates part of the texture
        data.
        """

        shape = data.shape
        data  = data.flatten(order='F')

        with self.bound():
            gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                               0,
                               offset[0],
                               offset[1],
                               offset[2],
                               shape[0],
                               shape[1],
                               shape[2],
                               self.baseFormat,
                               self.textureType,
                               data)
