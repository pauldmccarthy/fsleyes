#!/usr/bin/env python
#
# imagetexture.py - The ImageTexture class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageTexture` class, a 3D :class:`.Texture`
for storing a :class:`.Image` instance.
"""


import logging


import numpy     as np
import OpenGL.GL as gl

import fsl.utils.transform     as transform
import fsl.fsleyes.gl.routines as glroutines

import texture


log = logging.getLogger(__name__)


class ImageTexture(texture.Texture):
    """The ``ImageTexture`` class contains the logic required to create and
    manage a 3D texture which represents a :class:`.Image` instance.

    Once created, the :class:`.Image` instance is available as an attribute
    of an :class:`ImageTexture` object, called `image``. Additionally, a
    number of other attributes are added by the :meth:`__determineTextureType`
    method - see its documentation for more details.

    A number of texture settings can be configured through the following
    methods:

    .. autosummary::
       :nosignatures:

       set
       setInterp
       setPrefilter
       setResolution
       setVolume
       setNormalise
    """
    
    def __init__(self,
                 name,                 
                 image,
                 nvals=1,
                 normalise=False,
                 prefilter=None,
                 interp=gl.GL_NEAREST):
        """Create an :class:`ImageTexture`. A listener is added to the
        :attr:`.Image.data`  property, so that the texture data can be
        refreshed whenever the image data changes - see the
        :meth:`__imageDataChanged` method.
        
        :arg name:      A unique name for the texture.
        
        :arg image:     The :class:`.Image` instance.
          
        :arg nvals:     Number of values per voxel. For example. a normal MRI
                        or fMRI image contains only one value for each voxel.
                        However, DTI data contains three values per voxel.
        
        :arg normalise: If ``True``, the image data is normalised to lie in the
                        range ``[0.0, 1.0]``.
        
        :arg prefilter: An optional function which may perform any 
                        pre-processing on the data before it is copied to the 
                        GPU - see the :meth:`__prepareTextureData` method.
        """

        texture.Texture.__init__(self, name, 3)

        try:
            if nvals > 1 and image.shape[3] != nvals:
                raise RuntimeError()
        except:
            raise RuntimeError('Data shape mismatch: texture '
                               'size {} requested for '
                               'image shape {}'.format(nvals, image.shape))

        self.image        = image
        self.__nvals      = nvals
        self.__interp     = None
        self.__resolution = None
        self.__volume     = None
        self.__normalise  = None
        self.__prefilter  = prefilter
        # The __prefilter attribute is needed
        # by the __imageDataChanged method,
        # so we set it above. The other
        # attributes are configured in the
        # call to the set method, below.

        self.__name = '{}_{}'.format(type(self).__name__, id(self))
        self.image.addListener('data',
                               self.__name,
                               lambda *a: self.__imageDataChanged(),
                               weak=False)

        self.__imageDataChanged(False)
        self.set(interp=interp,
                 prefilter=prefilter,
                 resolution=None,
                 volume=None,
                 normalise=normalise)


    def destroy(self):
        """Must be called when this ``ImageTexture`` is no longer needed.
        Deletes the texture handle, and removes the listener on the
        :attr:`.Image.data` property.
        """

        texture.Texture.destroy(self)
        self.image.removeListener('data', self.__name)


    def setInterp(self, interp):
        """Sets the texture interpolation - either ``GL_NEAREST`` or
        ``GL_LINEAR``.
        """
        self.set(interp=interp)

        
    def setPrefilter(self, prefilter):
        """Sets the prefilter function - see :meth:`__init__`. """
        self.set(prefilter=prefilter)

        
    def setResolution(self, resolution):
        """Sets the image texture resolution - this value is passed to the
        :func:`.routines.subsample` function, in the
        :meth:`__prepareTextureData` method.
        """
        self.set(resolution=resolution)

        
    def setVolume(self, volume):
        """For 4D :class:`.Image` instances, specifies the volume to use
        as the 3D texture data.
        """
        self.set(volume=volume)

        
    def setNormalise(self, normalise):
        """Enable/disable normalisation - if ``True``, the image data is
        normalised to lie in the range ``[0, 1]`` before being stored as
        a texture.
        """
        self.set(normalise=normalise)

        
    def set(self, **kwargs):
        """Set any parameters on this ``ImageTexture``. Valid keyword
        arguments are:

        ============== ==========================
        ``interp``     See :meth:`setInterp`.
        ``prefilter``  See :meth:`setPrefilter`.
        ``resolution`` See :meth:`setResolution`.
        ``volume``     See :meth:`setVolume`.
        ``normalise``  See :meth:`setNormalise`.
        ============== ==========================
        """
        interp     = kwargs.get('interp',     self.__interp)
        prefilter  = kwargs.get('prefilter',  self.__prefilter)
        resolution = kwargs.get('resolution', self.__resolution)
        volume     = kwargs.get('volume',     self.__volume)
        normalise  = kwargs.get('normalise',  self.__normalise)

        changed = (interp     != self.__interp     or
                   prefilter  != self.__prefilter  or
                   resolution != self.__resolution or
                   volume     != self.__volume     or
                   normalise  != self.__normalise)

        if not changed:
            return
        
        self.__interp     = interp
        self.__prefilter  = prefilter
        self.__resolution = resolution
        self.__volume     = volume
            
        # If the data is of a type which cannot be
        # stored natively as an OpenGL texture, the
        # data is cast to a standard type, and
        # normalised - see _determineTextureType
        # and _prepareTextureData
        dtype = self.image.data.dtype
        self.__normalise = normalise or dtype not in (np.uint8,
                                                      np.int8,
                                                      np.uint16,
                                                      np.int16)

        if prefilter != self.__prefilter:
            self.__imageDataChanged(False)
 
        self.refresh()

        
    def refresh(self, *a):
        """(Re-)generates the OpenGL texture used to store the image data.
        """

        self.__determineTextureType()
        data = self.__prepareTextureData()

        # It is assumed that, for textures with more than one
        # value per voxel (e.g. RGB textures), the data is
        # arranged accordingly, i.e. with the voxel value
        # dimension the fastest changing
        if len(data.shape) == 4: self.textureShape = data.shape[1:]
        else:                    self.textureShape = data.shape

        log.debug('Refreshing 3D texture (id {}) for '
                  '{} (data shape: {})'.format(
                      self.getTextureHandle(),
                      self.getTextureName(),
                      self.textureShape))

        # The image data is flattened, with fortran dimension
        # ordering, so the data, as stored on the GPU, has its
        # first dimension as the fastest changing.
        data = data.ravel(order='F')

        # Enable storage of tightly packed data of any size (i.e.
        # our texture shape does not have to be divisible by 4).
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)

        self.bindTexture()

        # set interpolation routine
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           self.__interp)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           self.__interp)

        # Clamp texture borders to the edge
        # values - it is the responsibility
        # of the rendering logic to not draw
        # anything outside of the image space
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
        # _determineTextureType method.
        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        self.texIntFmt,
                        self.textureShape[0],
                        self.textureShape[1],
                        self.textureShape[2],
                        0,
                        self.texFmt,
                        self.texDtype,
                        data)

        self.unbindTexture()
    

    def __imageDataChanged(self, refresh=True):
        """Called when the :attr:`.Image.data` property changes. Refreshes
        the texture data accordingly.
        """

        data  = self.image.data

        if self.__prefilter is not None:
            data = self.__prefilter(data)
        
        self.__dataMin  = float(data.min())
        self.__dataMax  = float(data.max())         

        if refresh:
            self.refresh()


    def __determineTextureType(self):
        """Figures out how the image data should be stored as an OpenGL 3D
        texture.

        
        Regardless of its native data type, the image data is stored in an
        unsigned integer format. This method figures out the best data type to
        use - if the data is already in an unsigned integer format, it may be
        used as-is. Otherwise, the data needs to be cast and potentially
        normalised before it can be used as texture data.

        
        Internally (e.g. in GLSL shader code), the GPU automatically
        normalises texture data to the range ``[0.0, 1.0]``. This method
        therefore calculates an appropriate transformation matrix which may be
        used to transform these normalised values back to the raw data values.


        .. note:: OpenGL does different things to 3D texture data depending on
                  its type: unsigned integer types are normalised from ``[0,
                  INT_MAX]`` to ``[0, 1]``.

                  Floating point texture data types are, by default, *clamped*
                  (not normalised), to the range ``[0, 1]``! This could be
                  overcome by using a more recent versions of OpenGL, or by
                  using the ``ARB.texture_rg.GL_R32``F data format. Here, we
                  simply cast floating point data to an unsigned integer type,
                  normalise it to the appropriate range, and calculate a
                  transformation matrix to transform back to the data range.

        
        This method sets the following attributes on this ``ImageTexture``
        instance:

        ================== ==============================================
        ``texFmt``         The texture format (e.g. ``GL_RGB``,
                           ``GL_LUMINANCE``, etc).

        ``texIntFmt``      The internal texture format used by OpenGL for
                           storage (e.g. ``GL_RGB16``, ``GL_LUMINANCE8``,
                           etc).

        ``texDtype``       The raw type of the texture data (e.g.
                           ``GL_UNSIGNED_SHORT``)

        ``voxValXform``    An affine transformation matrix which encodes 
                           an offset and a scale, which may be used to 
                           transform the texture data from the range 
                           ``[0.0, 1.0]`` to its raw data range.

        ``invVoxValXform`` Inverse of ``voxValXform``.
        ================== ==============================================
        """        

        data  = self.image.data

        if self.__prefilter is not None:
            data = self.__prefilter(data)
        
        dtype = data.dtype
        dmin  = self.__dataMin
        dmax  = self.__dataMax

        # Signed data types are a pain in the arse.
        #
        # TODO It would be nice if you didn't have
        # to perform the data conversion/offset
        # for signed types.

        # Texture data type
        if   self.__normalise:   texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.uint8:  texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.int8:   texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.uint16: texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.int16:  texDtype = gl.GL_UNSIGNED_SHORT

        # The texture format
        if   self.__nvals == 1: texFmt = gl.GL_LUMINANCE
        elif self.__nvals == 2: texFmt = gl.GL_LUMINANCE_ALPHA
        elif self.__nvals == 3: texFmt = gl.GL_RGB
        elif self.__nvals == 4: texFmt = gl.GL_RGBA
        else:
            raise ValueError('Cannot create texture representation '
                             'for {} (nvals: {})'.format(self.tag,
                                                         self.__nvals))

        # Internal texture format
        if self.__nvals == 1:

            if   self.__normalise:   intFmt = gl.GL_LUMINANCE16
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16

        elif self.__nvals == 2:
            if   self.__normalise:   intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16_ALPHA16

        elif self.__nvals == 3:
            if   self.__normalise:   intFmt = gl.GL_RGB16
            elif dtype == np.uint8:  intFmt = gl.GL_RGB8
            elif dtype == np.int8:   intFmt = gl.GL_RGB8
            elif dtype == np.uint16: intFmt = gl.GL_RGB16
            elif dtype == np.int16:  intFmt = gl.GL_RGB16
            
        elif self.__nvals == 4:
            if   self.__normalise:   intFmt = gl.GL_RGBA16
            elif dtype == np.uint8:  intFmt = gl.GL_RGBA8
            elif dtype == np.int8:   intFmt = gl.GL_RGBA8
            elif dtype == np.uint16: intFmt = gl.GL_RGBA16
            elif dtype == np.int16:  intFmt = gl.GL_RGBA16 

        # Offsets/scales which can be used to transform from
        # the texture data (which may be offset or normalised)
        # back to the original voxel data
        if   self.__normalise:   offset =  dmin
        elif dtype == np.uint8:  offset =  0
        elif dtype == np.int8:   offset = -128
        elif dtype == np.uint16: offset =  0
        elif dtype == np.int16:  offset = -32768

        if   self.__normalise:   scale = dmax - dmin
        elif dtype == np.uint8:  scale = 255
        elif dtype == np.int8:   scale = 255
        elif dtype == np.uint16: scale = 65535
        elif dtype == np.int16:  scale = 65535

        voxValXform = transform.scaleOffsetXform(scale, offset)

        # This is all just for logging purposes
        if log.getEffectiveLevel() == logging.DEBUG:

            if   texDtype == gl.GL_UNSIGNED_BYTE:
                sTexDtype = 'GL_UNSIGNED_BYTE'
            elif texDtype == gl.GL_UNSIGNED_SHORT:
                sTexDtype = 'GL_UNSIGNED_SHORT' 
            
            if   texFmt == gl.GL_LUMINANCE:
                sTexFmt = 'GL_LUMINANCE'
            elif texFmt == gl.GL_LUMINANCE_ALPHA:
                sTexFmt = 'GL_LUMINANCE_ALPHA'
            elif texFmt == gl.GL_RGB:
                sTexFmt = 'GL_RGB'
            elif texFmt == gl.GL_RGBA:
                sTexFmt = 'GL_RGBA'
                
            if   intFmt == gl.GL_LUMINANCE8:
                sIntFmt = 'GL_LUMINANCE8'
            elif intFmt == gl.GL_LUMINANCE16:
                sIntFmt = 'GL_LUMINANCE16' 
            elif intFmt == gl.GL_LUMINANCE8_ALPHA8:
                sIntFmt = 'GL_LUMINANCE8_ALPHA8'
            elif intFmt == gl.GL_LUMINANCE16_ALPHA16:
                sIntFmt = 'GL_LUMINANCE16_ALPHA16'
            elif intFmt == gl.GL_RGB8:
                sIntFmt = 'GL_RGB8'
            elif intFmt == gl.GL_RGB16:
                sIntFmt = 'GL_RGB16'
            elif intFmt == gl.GL_RGBA8:
                sIntFmt = 'GL_RGBA8'
            elif intFmt == gl.GL_RGBA16:
                sIntFmt = 'GL_RGBA16' 
            
            log.debug('Image texture ({}) is to be stored as {}/{}/{} '
                      '(normalised: {} -  scale {}, offset {})'.format(
                          self.image,
                          sTexDtype,
                          sTexFmt,
                          sIntFmt,
                          self.__normalise,
                          scale,
                          offset))

        self.texFmt         = texFmt
        self.texIntFmt      = intFmt
        self.texDtype       = texDtype
        self.voxValXform    = voxValXform
        self.invVoxValXform = transform.invert(voxValXform)


    def __prepareTextureData(self):
        """This method prepares and returns the image data, ready to be
        used as GL texture data.
        
        This process potentially involves:
        
          - Resampling to a different resolution (see the
            :func:`.routines.subsample` function).
        
          - Pre-filtering (see the ``prefilter`` parameter to
            :meth:`__init__`).
        
          - Normalising (if the ``normalise`` parameter to :meth:`__init__`
            was True, or if the image data type cannot be used as-is).
        
          - Casting to a different data type (if the image data type cannot
            be used as-is).
        """

        image = self.image
        data  = image.data
        dtype = data.dtype

        volume     = self.__volume
        resolution = self.__resolution
        prefilter  = self.__prefilter
        normalise  = self.__normalise

        if volume is None:
            volume = 0

        if image.is4DImage() and self.__nvals == 1:
            data = data[..., volume]

        if resolution is not None:
            data = glroutines.subsample(data, resolution, image.pixdim)[0]
            
        if prefilter is not None:
            data = prefilter(data)
        
        if normalise:
            dmin = float(self.__dataMin)
            dmax = float(self.__dataMax)
            if dmax != dmin:
                data = (data - dmin) / (dmax - dmin)
            data = np.round(data * 65535)
            data = np.array(data, dtype=np.uint16)
            
        elif dtype == np.uint8:  pass
        elif dtype == np.int8:   data = np.array(data + 128,   dtype=np.uint8)
        elif dtype == np.uint16: pass
        elif dtype == np.int16:  data = np.array(data + 32768, dtype=np.uint16)

        return data
