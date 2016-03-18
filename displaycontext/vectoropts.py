#!/usr/bin/env python
#
# vectoropts.py - Defines the VectorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`VectorOpts`, :class:`LineVectorOpts`, and
:class:`RGBVectorOpts` classes, which contain options for displaying NIFTI1
vector images.
"""


import copy

import props

import fsl.data.image as fslimage
import                   volumeopts


class VectorOpts(volumeopts.Nifti1Opts):
    """The ``VectorOpts`` class is the base class for :class:`LineVectorOpts`,
    :class:`RGBVectorOpts`, and :class:`.TensorOpts`. It contains display
    settings which are common to each of them.
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


    cmap = props.ColourMap()
    """If an image is selected as the :attr:`colourImage`, this colour map
    is used to colour the vector voxels.
    """

    
    colourImage = props.Choice()
    """Colour vector voxels by the values contained in this image. Any image which
    is in the :class:`.OverlayList`, and which has the same voxel dimensions as
    the vector image can be selected for modulation. If a ``colourImage`` is
    selected, the :attr:`xColour`, :attr:`yColour`, :attr:`zColour`,
    :attr:`suppressX`, :attr:`suppressY`, and :attr:`suppressZ` properties are
    all ignored.
    """


    modulateImage  = props.Choice()
    """Modulate the vector colour brightness by another image. Any image which
    is in the :class:`.OverlayList`, and which has the same voxel dimensions as
    the vector image can be selected for modulation.
    """

    
    clipImage = props.Choice()
    """Clip voxels from the vector image according to another image. Any image
    which is in the :class:`.OverlayList`, and which has the same voxel
    dimensions as the vector image can be selected for clipping. The
    :attr:`clippingRange` dictates the value below which vector voxels are
    clipped.
    """ 

    
    clippingRange = props.Bounds(ndims=1)
    """Hide voxels for which the clip image value is outside of this range. """

    
    def __init__(self, *args, **kwargs):
        """Create a ``VectorOpts`` instance for the given image.  All
        arguments are passed through to the :class:`.Nifti1Opts`
        constructor.
        """
        
        volumeopts.Nifti1Opts.__init__(self, *args, **kwargs)

        self.__registered = self.getParent() is not None

        if self.__registered:
            
            self.overlayList.addListener('overlays',
                                         self.name,
                                         self.__overlayListChanged)
            self            .addListener('clipImage',
                                         self.name,
                                         self.__clipImageChanged)

            if not self.isSyncedToParent('modulateImage'):
                self.__refreshAuxImage('modulateImage')
            if not self.isSyncedToParent('clipImage'):
                self.__refreshAuxImage('clipImage')
            if not self.isSyncedToParent('colourImage'):
                self.__refreshAuxImage('colourImage') 

        else:
            self.__overlayListChanged()
            self.__clipImageChanged()


    def destroy(self):
        """Removes some property listeners, and calls the
        :meth:`.Nifti1Opts.destroy` method.
        """
        if self.__registered:
            self.overlayList.removeListener('overlays',  self.name)
            self            .removeListener('clipImage', self.name)

        volumeopts.Nifti1Opts.destroy(self)

        
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

        opts   = self.displayCtx.getOpts(image)
        minval = opts.dataMin
        maxval = opts.dataMax

        # Clipping works with <= and >=, so
        # we add an offset allowing the user
        # to configure the overlay such that
        # no voxels are clipped.
        distance = (maxval - minval) / 100.0

        self.clippingRange.xmin =  minval - distance
        self.clippingRange.xmax =  maxval + distance
        self.clippingRange.x    = [minval, maxval + distance]

        
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

            # an image can only be used to
            # modulate/clip/colour the vector
            # image if it shares the same
            # dimensions as said vector image.
            # 4D images are ok though.
            if overlay.shape[:3] != self.overlay.shape[:3]:
                continue

            options.append(overlay)
            
        prop.setChoices(options, instance=self)

        if val in options: setattr(self, imageName, val)
        else:              setattr(self, imageName, None)


class LineVectorOpts(VectorOpts):
    """The ``LineVectorOpts`` class contains settings for displaying vector
    images, using a line to represent the vector value at each voxel.
    """

    
    lineWidth = props.Int(minval=1, maxval=10, default=1)
    """Width of the line in pixels.
    """

    directed = props.Boolean(default=False)
    """If ``True``, the vector data is interpreted as directed. Otherwise,
    the vector data is assumed to be undirected.
    """

    
    def __init__(self, *args, **kwargs):
        """Create a ``LineVectorOpts`` instance. All arguments are passed
        through  to the :class:`VectorOpts` constructor.
        """

        kwargs['nounbind'] = ['directed']

        VectorOpts.__init__(self, *args, **kwargs)



class RGBVectorOpts(VectorOpts):
    """The ``RGBVectorOpts`` class contains settings for displaying vector
    images, using a combination of three colours to represent the vector value
    at each voxel.
    """

    interpolation = copy.copy(volumeopts.VolumeOpts.interpolation)
