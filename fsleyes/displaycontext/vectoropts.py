#!/usr/bin/env python
#
# vectoropts.py - Defines the VectorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`VectorOpts`, :class:`LineVectorOpts`, and
:class:`RGBVectorOpts` classes, which contain options for displaying NIFTI
vector images.
"""


import copy

import numpy as np

import fsleyes_props      as props
import fsl.data.image     as fslimage
import fsleyes.gl         as fslgl
import fsleyes.colourmaps as fslcm
from . import                niftiopts
from . import                volumeopts


class VectorOpts:
    """The ``VectorOpts`` class is a mixin for use with :class:`.DisplayOpts`
    sub-classes, providng properties and logic for displaying overlays which
    can be coloured according to XYZ orientations.
    """


    xColour = props.Colour(default=(1.0, 0.0, 0.0))
    """Colour used to represent the X vector magnitude."""


    yColour = props.Colour(default=(0.0, 1.0, 0.0))
    """Colour used to represent the Y vector magnitude."""


    zColour = props.Colour(default=(0.0, 0.0, 1.0))
    """Colour used to represent the Z vector magnitude."""


    suppressX = props.Boolean(default=False)
    """Do not use the X vector magnitude to colour vectors."""


    suppressY = props.Boolean(default=False)
    """Do not use the Y vector magnitude to colour vectors."""


    suppressZ = props.Boolean(default=False)
    """Do not use the Z vector magnitude to colour vectors."""


    suppressMode = props.Choice(('white', 'black', 'transparent'))
    """How vector direction colours should be suppressed. """


    normaliseColour = props.Boolean(default=False)
    """If ``True``, the vector values are normalised to uniform brightness.
    If ``False`` (the default), the vector XYZ values are used directly
    as RGB values.
    """


    def getVectorColours(self):
        """Prepares the colours that represent each direction.

        Returns:
          - a ``numpy`` array of size ``(3, 4)`` containing the
            RGBA colours that correspond to the ``x``, ``y``, and ``z``
            vector directions.

          - A ``numpy`` array of shape ``(4, 4)`` which encodes a scale
            and offset to be applied to the vector value before it
            is combined with the colours, encoding the current
            brightness and contrast settings.
        """
        display = self.display
        bri     = display.brightness / 100.0
        con     = display.contrast   / 100.0
        alpha   = display.alpha      / 100.0

        colours       = np.array([self.xColour, self.yColour, self.zColour])
        colours[:, 3] = alpha

        if   self.suppressMode == 'white':       suppress = [1, 1, 1, alpha]
        elif self.suppressMode == 'black':       suppress = [0, 0, 0, alpha]
        elif self.suppressMode == 'transparent': suppress = [0, 0, 0, 0]

        # Transparent suppression
        if self.suppressX: colours[0, :] = suppress
        if self.suppressY: colours[1, :] = suppress
        if self.suppressZ: colours[2, :] = suppress

        # Scale/offset for brightness/contrast.
        # Note: This code is a duplicate of
        # that found in ColourMapTexture.
        lo, hi = fslcm.briconToDisplayRange((0, 1), bri, con)

        if hi == lo: scale = 0.0000000000001
        else:        scale = hi - lo

        xform = np.identity(4, dtype=np.float32)
        xform[0, 0] = 1.0 / scale
        xform[0, 3] = -lo * xform[0, 0]

        return colours, xform


class NiftiVectorOpts(niftiopts.NiftiOpts, VectorOpts):
    """The ``NiftiVectorOpts`` class is the base class for
    :class:`LineVectorOpts`, :class:`RGBVectorOpts`, :class:`.TensorOpts`, and
    :class:`.SHOpts`. It contains display settings which are common to each of
    them.


    *A note on orientation*


    The :attr:`orientFlip` property allows you to flip the left-right
    orientation of line vectors, tensors, and SH functions. This option is
    necessary, because different tools may output vector data in different
    ways, depending on the image orientation.


    For images which are stored radiologically (with the X axis increasaing
    from right to left), the FSL tools (e.g. `dtifit`) will generate vectors
    which are oriented according to the voxel coordinate system. However, for
    neurologically stored images (X axis increasing from left to right), FSL
    tools generate vectors which are radiologically oriented, and thus are
    inverted with respect to the X axis in the voxel coordinate system.
    Therefore, in order to correctly display vectors from such an image, we
    must flip each vector about the X axis.


    This issue is also applicable to ``tensor`` and ``sh`` overlays.
    """


    orientFlip = props.Boolean(default=True)
    """If ``True``, individual vectors are flipped along the x-axis. This
    property is only applicable to the :class:`.LineVectorOpts`,
    :class:`.TensorOpts`, and :class:`.SHOpts` classes. See the
    :meth:`.NiftiOpts.getTransform` method for more information.

    This value defaults to ``True`` for images which have a neurological
    storage order, and ``False`` for radiological images.
    """


    cmap = props.ColourMap(prefix='fsleyes_')
    """If an image is selected as the :attr:`colourImage`, this colour map
    is used to colour the vector voxels.
    """


    colourImage = props.Choice()
    """Colour vector voxels by the values contained in this image. Any image which
    is in the :class:`.OverlayList`, and which has the same voxel dimensions
    as the vector image can be selected for colouring. If a ``colourImage``
    is selected, the :attr:`xColour`, :attr:`yColour`, :attr:`zColour`,
    :attr:`suppressX`, :attr:`suppressY`, and :attr:`suppressZ` properties are
    all ignored.
    """


    modulateImage  = props.Choice()
    """Modulate the vector colour brightness/alpha by another image. Any image
    which is in the :class:`.OverlayList`, and which has the same voxel
    dimensions as the vector image can be selected for modulation.
    """


    modulateMode = props.Choice(('brightness', 'alpha'))
    """Modulate either the brightness or transparency by the modulation image.
    """


    clipImage = props.Choice()
    """Clip voxels from the vector image according to another image. Any image
    which is in the :class:`.OverlayList`, and which has the same voxel
    dimensions as the vector image can be selected for clipping. The
    :attr:`clippingRange` dictates the value below which vector voxels are
    clipped.
    """


    clippingRange = props.Bounds(ndims=1)
    """Hide voxels for which the :attr:`clipImage` value is outside of this
    range.
    """


    modulateRange = props.Bounds(ndims=1, clamped=False)
    """Data range used in brightness/transparency modulation, when a
    :attr:`modulateImage` is in use.
    """


    colourRange = props.Bounds(ndims=1, clamped=False)
    """Data range used for colouring, when a :attr:`colourImage` is in use.
    """


    def __init__(self, image, *args, **kwargs):
        """Create a ``VectorOpts`` instance for the given image.  All
        arguments are passed through to the :class:`.NiftiOpts`
        constructor.
        """

        # The orientFlip property defaults to True
        # for neurologically stored images. We
        # give it this vale before calling __init__,
        # because  if this VectorOptse instance has
        # a parent, we want to inherit the parent's
        # value.
        self.orientFlip = image.isNeurological()

        niftiopts.NiftiOpts.__init__(self, image, *args, **kwargs)

        self.__registered = self.getParent() is not None

        if self.__registered:

            self.overlayList.addListener('overlays',
                                         self.name,
                                         self.__overlayListChanged)
            self            .addListener('clipImage',
                                         self.name,
                                         self.__clipImageChanged)
            self            .addListener('colourImage',
                                         self.name,
                                         self.__colourImageChanged)
            self            .addListener('modulateImage',
                                         self.name,
                                         self.__modulateImageChanged)

            if not self.isSyncedToParent('modulateImage'):
                self.__refreshAuxImage('modulateImage')
            if not self.isSyncedToParent('clipImage'):
                self.__refreshAuxImage('clipImage')
            if not self.isSyncedToParent('colourImage'):
                self.__refreshAuxImage('colourImage')

        else:
            self.__overlayListChanged()
            self.__clipImageChanged()
            self.__modulateImageChanged()
            self.__colourImageChanged()


    def destroy(self):
        """Removes some property listeners, and calls the
        :meth:`.NiftiOpts.destroy` method.
        """
        if self.__registered:
            self.overlayList.removeListener('overlays',      self.name)
            self            .removeListener('clipImage',     self.name)
            self            .removeListener('modulateImage', self.name)
            self            .removeListener('colourImage',   self.name)

        niftiopts.NiftiOpts.destroy(self)


    def __clipImageChanged(self, *a):
        """Called when the :attr:`clipImage` property changes. Updates
        the range of the :attr:`clippingRange` property.
        """
        self.__updateRange(self.clipImage, self.clippingRange, pad=True)


    def __modulateImageChanged(self, *a):
        """Called when the :attr:`modulateImage` property changes. Updates
        the range of the :attr:`modulateRange` property.
        """

        self.__updateRange(self.modulateImage, self.modulateRange)


    def __colourImageChanged(self, *a):
        """Called when the :attr:`colourImage` property changes. Updates
        the range of the :attr:`coluorRange` property.
        """

        self.__updateRange(self.colourImage, self.colourRange)


    def __updateRange(self, image, rangeobj, pad=False):
        """Used whenever :attr:`clipImage`, :attr:`modulateImage`, or
        :attr:`colourImage` change. Updates the :attr:`clippingRange`,
        :attr:`modulateRange`, or :attr:`colourRange` respectively.
        """

        if image is None: minval, maxval = 0, 1
        else:             minval, maxval = image.dataRange


        # Clipping works with <= and >=, so
        # we add an offset allowing the user
        # to configure the overlay such that
        # no voxels are clipped.
        if pad: pad = (maxval - minval) / 100.0
        else:   pad = 0

        rangeobj.xmin = minval - pad
        rangeobj.xmax = maxval + pad
        rangeobj.x    = [minval, maxval + pad]


    def __overlayListChanged(self, *a):
        """Called when the overlay list changes. Updates the :attr:`modulateImage`,
        :attr:`colourImage` and :attr:`clipImage` properties so that they
        contain a list of overlays which could be used to modulate the vector
        image.
        """

        overlays = self.displayCtx.getOrderedOverlays()

        # the image for this VectorOpts
        # instance has been removed
        if self.overlay not in overlays:
            return

        self.__refreshAuxImage('modulateImage')
        self.__refreshAuxImage('clipImage')
        self.__refreshAuxImage('colourImage')


    def __refreshAuxImage(self, imageName):
        """Updates the named image property (:attr:`modulateImage`,
        :attr:`colourImage` or :attr:`clipImage`) so that it contains a list
        of overlays which could be used to modulate the vector image.
        """

        prop     = self.getProp(imageName)
        val      = getattr(self, imageName)
        overlays = self.displayCtx.getOrderedOverlays()

        options = [None]

        for overlay in overlays:

            # It doesn't make sense to
            # modulate/clip/colour the
            # image by itself.
            if overlay is self.overlay:
                continue

            # The modulate/clip/colour
            # images must be images.
            if not isinstance(overlay, fslimage.Image):
                continue

            options.append(overlay)

        prop.setChoices(options, instance=self)

        if val in options: setattr(self, imageName, val)
        else:              setattr(self, imageName, None)


class LineVectorOpts(NiftiVectorOpts):
    """The ``LineVectorOpts`` class contains settings for displaying vector
    images, using a line to represent the vector value at each voxel.
    """


    lineWidth = props.Real(minval=0.1, maxval=10, default=1, clamped=False)
    """Width of the line in pixels.
    """

    directed = props.Boolean(default=False)
    """If ``True``, the vector data is interpreted as directed. Otherwise,
    the vector data is assumed to be undirected.
    """

    modulateMode = props.Choice(('brightness', 'alpha', 'lineLength'))
    """Overwrites :attr:`NiftiVectorOpts.modulateMode`.

    Modulate the brightness, transparency, or line length by the modulation
    image.  When set to ``'lineLength'``, this is applied after the
    :attr:`unitLength` and before the :attr:`lengthScale` properties.
    """


    unitLength = props.Boolean(default=True)
    """If ``True``, each vector is scaled so that it has a length of
    ``1 * lengthScale`` (or 0.5 if ``directed`` is ``True``).
    """


    lengthScale = props.Percentage(minval=10, maxval=500, default=100)
    """Length scaling factor. """


    def __init__(self, *args, **kwargs):
        """Create a ``LineVectorOpts`` instance. All arguments are passed
        through  to the :class:`VectorOpts` constructor.
        """

        kwargs['nounbind'] = ['directed', 'unitLength', 'lengthScale']

        NiftiVectorOpts.__init__(self, *args, **kwargs)


class RGBVectorOpts(NiftiVectorOpts):
    """The ``RGBVectorOpts`` class contains settings for displaying vector
    images, using a combination of three colours to represent the vector value
    at each voxel.
    """


    interpolation = copy.copy(volumeopts.VolumeOpts.interpolation)
    """Apply interpolation to the image data. """


    unitLength = props.Boolean(default=False)
    """Alias for :attr:`VectorOpts.normaliseColour`. Not used internally,
    kept for compatibility.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``RGBVectorOpts`` instance. All arguments are passed
        through  to the :class:`VectorOpts` constructor.
        """

        # unitLength is an alias for normaliseColour,
        # kept for compatibility.
        self.bindProps('unitLength', self, 'normaliseColour')

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        kwargs['nounbind'] = ['interpolation']
        NiftiVectorOpts.__init__(self, *args, **kwargs)
