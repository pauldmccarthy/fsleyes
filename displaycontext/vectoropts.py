#!/usr/bin/env python
#
# vectoropts.py - Defines the VectorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`VectorOpts` class, which contains display
options for rendering :class:`.GLVector` instances.
"""

import copy

import props

import fsl.data.image as fslimage
import                   volumeopts


class VectorOpts(volumeopts.ImageOpts):


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


    modulate  = props.Choice()
    """Modulate the vector colours by another image."""

    
    # TODO This is currently a percentage
    # of the modulation image data range.
    # It should be an absolute value
    modThreshold = props.Percentage(default=0.0)
    """Hide voxels for which the modulation value is below this threshold."""

    
    def __init__(self, *args, **kwargs):
        """Create a ``VectorOpts`` instance for the given image.

        See the :class:`.ImageOpts` documentation for more details.
        """
        
        volumeopts.ImageOpts.__init__(self, *args, **kwargs)

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__overlayListChanged)
        
        self.__overlayListChanged()


    def destroy(self):
        self.overlayList.removeListener('overlays', self.name)

        for overlay in self.overlayList:
            display = self.displayCtx.getDisplay(overlay)
            display.removeListener('name', self.name)

        volumeopts.ImageOpts.destroy(self)

        
    def __overlayListChanged(self, *a):
        """Called when the overlay list changes. Updates the ``modulate``
        property so that it contains a list of overlays which could be used
        to modulate the vector image.
        """
        
        modProp  = self.getProp('modulate')
        modVal   = self.modulate
        overlays = self.displayCtx.getOrderedOverlays()

        # the image for this VectorOpts
        # instance has been removed
        if self.overlay not in overlays:
            self.overlayList.removeListener('overlays', self.name)
            return

        modOptions = [None]

        for overlay in overlays:
            
            # It doesn't make sense to
            # modulate the image by itself
            if overlay is self.overlay:
                continue

            # The modulate image must
            # be an image. Duh.
            if not isinstance(overlay, fslimage.Image):
                continue

            # an image can only be used to modulate
            # the vector image if it shares the same
            # dimensions as said vector image
            if overlay.shape != self.overlay.shape[:3]:
                continue

            modOptions.append(overlay)
                
            overlay.addListener('name',
                                self.name,
                                self.__overlayListChanged,
                                overwrite=True)
            
        modProp.setChoices(modOptions, instance=self)

        if modVal in overlays: self.modulate = modVal
        else:                  self.modulate = None


class LineVectorOpts(VectorOpts):

    lineWidth = props.Int(minval=1, maxval=10, default=1)

    directed  = props.Boolean(default=False)
    """

    The directed property cannot be unbound across multiple LineVectorOpts
    instances, as it affects the OpenGL representation
    """

    def __init__(self, *args, **kwargs):

        kwargs['nounbind'] = ['directed']

        VectorOpts.__init__(self, *args, **kwargs)



class RGBVectorOpts(VectorOpts):

    interpolation = copy.copy(volumeopts.VolumeOpts.interpolation)
