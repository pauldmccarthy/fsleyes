#!/usr/bin/env python
#
# data.py - Functions for preparing OpenGL texture data.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for working with OpenGL texture data:

.. autosummary::
   :nosignatures:

   numTextureDims
   canUseFloatTextures
   oneChannelFormat
   getTextureType
   prepareData
"""


import logging
import inspect

import numpy                       as np
import OpenGL.GL                   as gl
import OpenGL.extensions           as glexts
import OpenGL.GL.ARB.texture_float as arbtf

import fsl.utils.memoize           as memoize
import fsl.transform.affine        as affine
import fsleyes.gl.routines         as glroutines


log = logging.getLogger(__name__)


# Used for log messages
GL_TYPE_NAMES = {

    gl.GL_UNSIGNED_BYTE       : 'GL_UNSIGNED_BYTE',
    gl.GL_UNSIGNED_SHORT      : 'GL_UNSIGNED_SHORT',
    gl.GL_FLOAT               : 'GL_FLOAT',

    gl.GL_ALPHA               : 'GL_ALPHA',
    gl.GL_RED                 : 'GL_RED',
    gl.GL_LUMINANCE           : 'GL_LUMINANCE',
    gl.GL_RGB                 : 'GL_RGB',
    gl.GL_RGBA                : 'GL_RGBA',

    gl.GL_LUMINANCE8          : 'GL_LUMINANCE8',
    gl.GL_LUMINANCE16         : 'GL_LUMINANCE16',
    arbtf.GL_LUMINANCE16F_ARB : 'GL_LUMINANCE16F',
    arbtf.GL_LUMINANCE32F_ARB : 'GL_LUMINANCE32F',
    gl.GL_R32F                : 'GL_R32F',

    gl.GL_ALPHA8              : 'GL_ALPHA8',

    gl.GL_R8                  : 'GL_R8',
    gl.GL_R16                 : 'GL_R16',

    gl.GL_RGB8                : 'GL_RGB8',
    gl.GL_RGB16               : 'GL_RGB16',
    gl.GL_RGB32F              : 'GL_RGB32F',

    gl.GL_RGBA8               : 'GL_RGBA8',
    gl.GL_RGBA16              : 'GL_RGBA16',
    gl.GL_RGBA32F             : 'GL_RGBA32F',
}


def _makeInstance(dtype):
    """Used by :func:`oneChannelFormat` and :func:`getTextureType`.  If a
    ``numpy.dtype`` class is given, converts it into an instance.
    """
    if inspect.isclass(dtype):
        dtype = np.zeros([0], dtype=dtype).dtype
    return dtype


def numTextureDims(shape):
    """Given a 3D image shape, returns the number of dimensions needd
    to store the image as a texture - either ``2`` or ``3``.

    :arg shape: 3D image shape
    :returns:   2 if a 2D texture can be used to store the image data,
                3 otherwise.
    """
    max3d = gl.glGetInteger(gl.GL_MAX_3D_TEXTURE_SIZE)
    max2d = gl.glGetInteger(gl.GL_MAX_TEXTURE_SIZE)

    def checklim(shape, lim):
        if any([d > lim for d in shape]):
            raise RuntimeError(
                'Cannot create an OpenGL texture for {} - it exceeds '
                'the hardware limits on this platform (2D: {}, 3D: {}'
                .format(shape, max2d, max3d))

    shape = [d for d in shape[:3] if d > 1]

    # force scalar/vector shape to be 2D
    if   len(shape) == 0: shape = [1, 1]
    elif len(shape) == 1: shape = [shape[0], 1]

    if len(shape) == 3: checklim(shape, max3d)
    else:               checklim(shape, max2d)

    return len(shape)


@memoize.memoize
def canUseFloatTextures(nvals=1):
    """Returns ``True`` if this GL environment supports floating
    point textures, ``False`` otherwise. The test is based on the
    availability of the ``ARB_texture_float`` extension.

    :arg nvals: Number of values per voxel

    :returns: A tuple containing:

                - ``True`` if floating point textures are supported,
                  ``False`` otherwise

                - The base texture format to use (``None`` if floating
                  point textures are not supported)

                - The internal texture format to use  (``None`` if
                  floating point textures are not supported)
    """

    # We need the texture_float extension. The
    # texture_rg extension just provides some
    # nicer/more modern data types, but is not
    # necessary.
    floatSupported = glexts.hasExtension('GL_ARB_texture_float')
    rgSupported    = glexts.hasExtension('GL_ARB_texture_rg')

    if not floatSupported:
        return False, None, None

    if rgSupported:
        if   nvals == 1: baseFmt = gl.GL_RED
        elif nvals == 3: baseFmt = gl.GL_RGB
        elif nvals == 4: baseFmt = gl.GL_RGBA

        if   nvals == 1: intFmt  = gl.GL_R32F
        elif nvals == 3: intFmt  = gl.GL_RGB32F
        elif nvals == 4: intFmt  = gl.GL_RGBA32F

        return True, baseFmt, intFmt

    else:

        if   nvals == 1: baseFmt = gl.GL_LUMINANCE
        elif nvals == 3: baseFmt = gl.GL_RGB
        elif nvals == 4: baseFmt = gl.GL_RGBA

        if   nvals == 1: intFmt  = arbtf.GL_LUMINANCE32F_ARB
        elif nvals == 3: intFmt  = gl.GL_RGB32F
        elif nvals == 4: intFmt  = gl.GL_RGBA32F

        return True, baseFmt, intFmt


@memoize.memoize
def oneChannelFormat(dtype):
    """Determines suitable one-channel base and internal texture formats
    to use for the given ``numpy`` data type.

    :return: A tuple containing:

               - the base texture format to use
               - the internal texture format to use

    .. note:: This is used by the :func:`getTextureType` function. The
              returned formats may be ignored for floating point data
              types, depending on whether floating point textures are
              supported - see :func:`canUseFloatTextures`.
    """

    # Make sure we have a numpy dtype
    # *instance*, and not a class.
    dtype = _makeInstance(dtype)

    floatSupported = glexts.hasExtension('GL_ARB_texture_float')
    rgSupported    = glexts.hasExtension('GL_ARB_texture_rg')
    nbits          = dtype.itemsize * 8

    if rgSupported:
        if nbits == 8: return gl.GL_RED, gl.GL_R8
        else:          return gl.GL_RED, gl.GL_R16

    # GL_RED does not exist in old OpenGLs -
    # we have to use luminance instead.
    else:
        if nbits == 8:
            return gl.GL_LUMINANCE, gl.GL_LUMINANCE8

        # But GL_LUMINANCE is deprecated in GL 3.x,
        # and some more recent GL drivers seem to
        # have trouble displaying GL_LUMINANCE16
        # textures - displayting them at what seems
        # to be a down-sampled (e.g. using a 4 bit
        # storage format) version of the data. So we
        # store the data as floating point if we can.
        elif floatSupported:
            return gl.GL_LUMINANCE, arbtf.GL_LUMINANCE16F_ARB

        # Hopefully float textures are supported
        # on recent GL drivers which don't support
        # LUMINANCE_16
        else:
            return gl.GL_LUMINANCE, gl.GL_LUMINANCE16


@memoize.memoize
def getTextureType(normalise, dtype, nvals):
    """Figures out the GL data type, and the base/internal texture
    formats in which the specified data should be stored.


    This function just figures out the data types which should be used to
    store the data as a texture. Any necessary data conversion/transformation
    is performed by the :func:`prepareData` method.


    The data can be stored as a GL texture as-is if:

      - it is of type ``uint8`` or ``uint16``

      - it is of type ``float32``, *and* this GL environment has support
        for floating point textures. Support for floating point textures
        is determined by the :func:`canUseFlotaTextures` function.


    In all other cases, the data needs to be converted to a supported data
    type, and potentially normalised, before it can be used as texture
    data.  If floating point textures are available, the data is converted
    to float32. Otherwise, the data is converted to ``uint16``, and
    normalised to take the full ``uint16`` data range (``0-65535``), and a
    transformation matrix is saved, allowing transformation of this
    normalised data back to its original data range.


    .. note:: OpenGL does different things to texture data depending on
              its type: unsigned integer types are normalised from ``[0,
              INT_MAX]`` to ``[0, 1]``.

              Floating point texture data types are, by default, *clamped*
              (not normalised), to the range ``[0, 1]``! We can overcome by
              this by using a true floating point texture, which is
              accomplished by using one of the data types provided by the
              ``ARB_texture_float`` extension. If this extension is not
              available, we have no choice but to normalise the data.


    :arg normalise: Whether the data is to be normalised or not

    :arg dtype:     The original data type (e.g. ``np.uint8``)

    :arg nvals:     Number of values per voxel. Must be either ``1``,
                    ``3``, or ``4``.

    :returns:       A tuple containing:

                     - The raw type of the texture data
                       (e.g. ``GL_UNSIGNED_SHORT``)

                     - The texture format (e.g. ``GL_RGB``, ``GL_LUMINANCE``,
                       etc).

                     - The internal texture format used by OpenGL for storage
                       (e.g. ``GL_RGB16``, ``GL_LUMINANCE8``, etc).
    """

    dtype = _makeInstance(dtype)

    floatTextures, fBaseFmt, fIntFmt = canUseFloatTextures(nvals)
    ocBaseFmt, ocIntFmt              = oneChannelFormat(dtype)
    isFloat                          = issubclass(dtype.type, np.floating)

    # Signed data types are a pain in the arse.
    # We have to store them as unsigned, and
    # apply an offset.

    # Note: Throughout this function, it is assumed
    #       that if the data type is not supported,
    #       then the normalise flag will have been
    #       set to True.

    # Data type
    if   normalise:          texDtype = gl.GL_UNSIGNED_SHORT
    elif dtype == np.uint8:  texDtype = gl.GL_UNSIGNED_BYTE
    elif dtype == np.int8:   texDtype = gl.GL_UNSIGNED_BYTE
    elif dtype == np.uint16: texDtype = gl.GL_UNSIGNED_SHORT
    elif dtype == np.int16:  texDtype = gl.GL_UNSIGNED_SHORT
    elif floatTextures:      texDtype = gl.GL_FLOAT

    # Base texture format
    if floatTextures and isFloat: baseFmt = fBaseFmt
    elif nvals == 1:              baseFmt = ocBaseFmt
    elif nvals == 3:              baseFmt = gl.GL_RGB
    elif nvals == 4:              baseFmt = gl.GL_RGBA

    # Internal texture format
    if nvals == 1:
        if   normalise:          intFmt = ocIntFmt
        elif dtype == np.uint8:  intFmt = ocIntFmt
        elif dtype == np.int8:   intFmt = ocIntFmt
        elif dtype == np.uint16: intFmt = ocIntFmt
        elif dtype == np.int16:  intFmt = ocIntFmt
        elif floatTextures:      intFmt = fIntFmt

    elif nvals == 3:
        if   normalise:          intFmt = gl.GL_RGB16
        elif dtype == np.uint8:  intFmt = gl.GL_RGB8
        elif dtype == np.int8:   intFmt = gl.GL_RGB8
        elif dtype == np.uint16: intFmt = gl.GL_RGB16
        elif dtype == np.int16:  intFmt = gl.GL_RGB16
        elif floatTextures:      intFmt = fIntFmt

    elif nvals == 4:
        if   normalise:          intFmt = gl.GL_RGBA16
        elif dtype == np.uint8:  intFmt = gl.GL_RGBA8
        elif dtype == np.int8:   intFmt = gl.GL_RGBA8
        elif dtype == np.uint16: intFmt = gl.GL_RGBA16
        elif dtype == np.int16:  intFmt = gl.GL_RGBA16
        elif floatTextures:      intFmt = fIntFmt

    return texDtype, baseFmt, intFmt


def prepareData(data,
                prefilter=None,
                prefilterRange=None,
                resolution=None,
                scales=None,
                normalise=None,
                normaliseRange=None):
    """This function prepares and returns the given ``data``, ready to be
    used as GL texture data.

    This process potentially involves:

      - Resampling to a different resolution (see the
        :func:`.routines.subsample` function).

      - Pre-filtering (see the ``prefilter`` parameter to
        :meth:`__init__`).

      - Normalising (if the ``normalise`` parameter to :meth:`__init__`
        was ``True``, or if the data type cannot be used as-is).

      - Casting to a different data type (if the data type cannot be used
        as-is).

    :returns: A tuple containing:

                - A ``numpy`` array containing the image data, ready to be
                   copied to the GPU.

                - An affine transformation matrix which encodes an offset
                  and a scale, which may be used to transform the texture
                  data from the range ``[0.0, 1.0]`` to its raw data
                  range.

                - Inverse of ``voxValXform``.
    """

    dtype         = data.dtype
    floatTextures = canUseFloatTextures()

    if normalise: dmin, dmax = normaliseRange
    else:         dmin, dmax = 0, 0

    if normalise                  and \
       prefilter      is not None and \
       prefilterRange is not None:
        dmin, dmax = prefilterRange(dmin, dmax)

    # Offsets/scales which can be used to transform from
    # the texture data (which may be offset or normalised)
    # back to the original voxel data
    if   normalise:          offset =  dmin
    elif dtype == np.uint8:  offset =  0
    elif dtype == np.int8:   offset = -128
    elif dtype == np.uint16: offset =  0
    elif dtype == np.int16:  offset = -32768
    elif floatTextures:      offset = 0

    if   normalise:          scale = dmax - dmin
    elif dtype == np.uint8:  scale = 255
    elif dtype == np.int8:   scale = 255
    elif dtype == np.uint16: scale = 65535
    elif dtype == np.int16:  scale = 65535
    elif floatTextures:      scale = 1

    # If the data range is 0 (min == max)
    # we just set an identity xform
    if scale == 0:
        voxValXform    = np.eye(4)
        invVoxValXform = np.eye(4)

    # Otherwise we save a transformation
    # from the texture values back to the
    # original data range. Note that if
    # storing floating point data, this
    # will be an identity transform.
    else:
        invScale       = 1.0 / scale
        voxValXform    = affine.scaleOffsetXform(scale, offset)
        invVoxValXform = affine.scaleOffsetXform(
            invScale,
            -offset * invScale)

    if resolution is not None:
        data = glroutines.subsample(data, resolution, pixdim=scales)[0]

    if prefilter is not None:
        data = prefilter(data)

    # TODO if FLOAT_TEXTURES, you should
    #      save normalised values as float32
    if normalise:

        log.debug('Normalising to range {} - {}'.format(dmin, dmax))

        if dmax != dmin:
            data = np.clip((data - dmin) / float(dmax - dmin), 0, 1)

        data = np.round(data * 65535)
        data = np.array(data, dtype=np.uint16)

    elif dtype == np.uint8:  pass
    elif dtype == np.int8:   data = np.array(data + 128,   dtype=np.uint8)
    elif dtype == np.uint16: pass
    elif dtype == np.int16:  data = np.array(data + 32768, dtype=np.uint16)
    elif floatTextures and data.dtype != np.float32:
        data = np.array(data, dtype=np.float32)

    return data, voxValXform, invVoxValXform
