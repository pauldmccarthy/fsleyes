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

import fsleyes_props   as props
import fsl.data.image  as fslimage
import fsleyes.gl      as fslgl
from . import             niftiopts
from . import             volumeopts


class VectorOpts(niftiopts.NiftiOpts):
    """The ``VectorOpts`` class is the base class for :class:`LineVectorOpts`,
    :class:`RGBVectorOpts`, :class:`.TensorOpts`, and :class:`.SHOpts`. It
    contains display settings which are common to each of them.


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


    orientFlip = props.Boolean(default=True)
    """If ``True``, individual vectors are flipped along the x-axis. This
    property is only applicable to the :class:`.LineVectorOpts`,
    :class:`.TensorOpts`, and :class:`.SHOpts` classes. See the
    :meth:`.NiftiOpts.getTransform` method for more information.

    This value defaults to ``True`` for images which have a neurological
    storage order, and ``False`` for radiological images.
    """


    cmap = props.ColourMap()
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
    """Modulate either the brightness or transparency bu the modulation image.
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


    def destroy(self):
        """Removes some property listeners, and calls the
        :meth:`.NiftiOpts.destroy` method.
        """
        if self.__registered:
            self.overlayList.removeListener('overlays',      self.name)
            self            .removeListener('clipImage',     self.name)
            self            .removeListener('modulateImage', self.name)

        niftiopts.NiftiOpts.destroy(self)


    def __clipImageChanged(self, *a):
        """Called when the :attr:`clipImage` property changes. Updates
        the range of the :attr:`clippingRange` property.
        """

        image = self.clipImage

        if image is None:
            self.clippingRange.xmin = 0
            self.clippingRange.xmax = 1
            self.clippingRange.x    = [0, 1]
            return

        minval, maxval = image.dataRange

        # Clipping works with <= and >=, so
        # we add an offset allowing the user
        # to configure the overlay such that
        # no voxels are clipped.
        distance = (maxval - minval) / 100.0

        self.clippingRange.xmin =  minval - distance
        self.clippingRange.xmax =  maxval + distance
        self.clippingRange.x    = [minval, maxval + distance]


    def __modulateImageChanged(self, *a):
        """Called when the :attr:`modulateImage` property changes. Updates
        the range of the :attr:`modulateRange` property.
        """

        image = self.modulateImage

        if image is None: minval, maxval = 0, 1
        else:             minval, maxval = image.dataRange

        self.modulateRange.xmin = minval
        self.modulateRange.xmax = maxval
        self.modulateRange.x    = [minval, maxval]


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


class LineVectorOpts(VectorOpts):
    """The ``LineVectorOpts`` class contains settings for displaying vector
    images, using a line to represent the vector value at each voxel.
    """


    lineWidth = props.Real(minval=0.1, maxval=10, default=1, clamped=True)
    """Width of the line in pixels.
    """

    directed = props.Boolean(default=False)
    """If ``True``, the vector data is interpreted as directed. Otherwise,
    the vector data is assumed to be undirected.
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

        VectorOpts.__init__(self, *args, **kwargs)


class RGBVectorOpts(VectorOpts):
    """The ``RGBVectorOpts`` class contains settings for displaying vector
    images, using a combination of three colours to represent the vector value
    at each voxel.
    """


    interpolation = copy.copy(volumeopts.VolumeOpts.interpolation)
    """Apply interpolation to the image data. """


    unitLength = props.Boolean(default=False)
    """If ``True``, the vector data is scaled so it has length 1. """


    def __init__(self, *args, **kwargs):
        """Create a ``RGBVectorOpts`` instance. All arguments are passed
        through  to the :class:`VectorOpts` constructor.
        """

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        kwargs['nounbind'] = ['interpolation']
        VectorOpts.__init__(self, *args, **kwargs)
