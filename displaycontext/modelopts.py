#!/usr/bin/env python
#
# modelopts.py - The ModelOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ModelOpts` class, which defines settings
for displaying :class:`.Model` overlays.
"""


import copy

import numpy as np

import props

import display                as fsldisplay

import fsl.fsleyes.colourmaps as colourmaps
import fsl.data.image         as fslimage
import fsl.utils.transform    as transform

import volumeopts


class ModelOpts(fsldisplay.DisplayOpts):
    """The ``ModelOpts`` class defines settings for displaying :class:`.Model`
    overlays.
    """

    colour = props.Colour()
    """The model colour. """

    
    outline = props.Boolean(default=False)
    """If ``True``, an outline of the model is shown. Otherwise the model is
    filled.
    """

    
    outlineWidth = props.Real(minval=0, maxval=1, default=0.25, clamped=True)
    """If :attr:`outline` is ``True``, this property defines the width of the
    outline.
    """
    

    showName = props.Boolean(default=False)
    """If ``True``, the model name is shown alongside the model. """

    
    refImage = props.Choice()
    """A reference :class:`.Image` instance which the model coordinates are
    in terms of.

    For example, if this :class:`.Model` represents the segmentation of a
    sub-cortical region from a T1 image, you would set the ``refImage`` to that
    T1 image.

    Any :class:`.Image` instance in the :class:`.OverlayList` may be chosen
    as the reference image.
    """

    
    coordSpace = copy.copy(volumeopts.ImageOpts.transform)
    """If :attr:`refImage` is not ``None``, this property defines the
    reference image coordinate space in whihc the model coordinates are
    defined (i.e. voxels, scaled voxels, or world coordinates).
    """

    
    transform = copy.copy(volumeopts.ImageOpts.transform)
    """If :attr:`refImage` is not ``None``, this property is bound to 
    the :attr:`~.ImageOpts.transform` property of the reference image
    :class:`.ImageOpts` instance.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``ModelOpts`` instance. All arguments are passed through
        to the :class:`.DisplayOpts` constructor.
        """

        # Create a random, highly
        # saturated colour
        colour      = colourmaps.randomBrightColour()
        self.colour = np.concatenate((colour, [1.0]))

        nounbind = kwargs.get('nounbind', [])
        nounbind.extend(['refImage', 'coordSpace', 'transform'])
        kwargs['nounbind'] = nounbind
 
        # But create that colour before
        # base class initialisation, as
        # there may be a parent colour
        # value which will override the
        # one we generated above.
        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)

        self.__oldRefImage = None

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__overlayListChanged)

        # This attribute tracks the name of the
        # space-related property (refImage,
        # coordSpace, or transform) which most
        # recently changed. It is updated by
        # the corresponding listener callbacks,
        # and used by the transformDisplayLocation
        # method.
        self.__lastPropChanged = None
        
        self.addListener('refImage',   self.name, self.__refImageChanged)
        self.addListener('transform',  self.name, self.__transformChanged)
        self.addListener('coordSpace', self.name, self.__coordSpaceChanged)
        
        self.__overlayListChanged()
        self.__updateBounds()


    def destroy(self):
        """Removes some property listeners, and calls the
        :meth:`.DisplayOpts.destroy` method.
        """
        self.overlayList.removeListener('overlays', self.name)

        for overlay in self.overlayList:
            display = self.displayCtx.getDisplay(overlay)
            display.removeListener('name', self.name)

        fsldisplay.DisplayOpts.destroy(self)


    def getReferenceImage(self):
        """Overrides :meth:`.DisplayOpts.getReferenceIamge`.

        If a :attr:`refImage` is selected, it is returned. Otherwise,``None``
        is returned.
        """
        return self.refImage

    
    def getCoordSpaceTransform(self):
        """Returns a transformation matrix which can be used to transform
        the :class:`.Model` vertex coordinates into the display coordinate
        system.

        If no :attr:`refImage` is selected, this method returns ``None``.
        """

        if self.refImage is None or self.coordSpace == self.transform:
            return None

        opts = self.displayCtx.getOpts(self.refImage)

        return opts.getTransform(self.coordSpace, self.transform)


    def transformDisplayLocation(self, oldLoc):
        """If the :attr:`refImage`, :attr:`coordSpace` or :attr:`transform`
        properties have changed, this method will transform the specified
        location from the old :class:`.Model` display coordinate system to
        the new model display coordinate system.
        """

        newLoc   = oldLoc
        propName = self.__lastPropChanged
        
        if propName == 'refImage':

            refImage    = self.refImage
            oldRefImage = self.getLastValue('refImage')

            if refImage is None and oldRefImage is None:
                pass

            elif oldRefImage is None:
                refOpts = self.displayCtx.getOpts(refImage)
                newLoc  = refOpts.transformCoords([oldLoc],
                                                  self.coordSpace,
                                                  'display')[0]

            elif refImage is None:
                if oldRefImage is not None:
                    oldRefOpts = self.displayCtx.getOpts(oldRefImage)
                    newLoc     = oldRefOpts.transformCoords([oldLoc],
                                                            'display',
                                                            self.coordSpace)[0]

        elif propName == 'coordSpace':
            if self.refImage is not None:
                refOpts  = self.displayCtx.getOpts(self.refImage)
                worldLoc = refOpts.transformCoords(
                    [oldLoc],
                    self.getLastValue('coordSpace'),
                    'world')[0]
                newLoc   = refOpts.transformCoords(
                    [worldLoc],
                    'world',
                    self.coordSpace)[0]

        elif propName == 'transform':

            if self.refImage is not None:
                refOpts = self.displayCtx.getOpts(self.refImage)
                newLoc  = refOpts.transformDisplayLocation(oldLoc)

        return newLoc


    def __transformChanged(self, *a):
        """Called when the :attr:`transfrom` property changes.
        Calls :meth:`__updateBounds`.
        """
        self.__lastPropChanged = 'transform'
        self.__updateBounds()


    def __coordSpaceChanged(self, *a):
        """Called when the :attr:`coordSpace` property changes.
        Calls :meth:`__updateBounds`.
        """ 
        self.__lastPropChanged = 'coordSpace'
        self.__updateBounds()


    def __refImageChanged(self, *a):
        """Called when the :attr:`refImage` property changes.  Configures the
        :attr:`transform` property to track the :attr:`~.ImageOpts.transform`
        property of the :class:`.ImageOpts` instance associated with the new
        reference image, and calls :meth:`__updateBounds`.
        """

        # TODO You are not tracking changes to the
        # refImage overlay type -  if this changes,
        # you will need to re-bind to the transform
        # property of the new DisplayOpts instance

        self.__lastPropChanged = 'refImage'

        if self.__oldRefImage is not None and \
           self.__oldRefImage in self.overlayList:
            
            opts = self.displayCtx.getOpts(self.__oldRefImage)
            self.unbindProps('transform', opts)

        self.__oldRefImage = self.refImage

        if self.refImage is not None:
            opts = self.displayCtx.getOpts(self.refImage)
            self.bindProps('transform', opts)

        self.__updateBounds()


    def __updateBounds(self):
        """Called whenever any of the :attr:`refImage`, :attr:`coordSpace`, 
        or :attr:`transform` properties change.

        Updates the :attr:`.DisplayOpts.bounds` property accordingly.
        """

        lo, hi = self.overlay.getBounds()
        xform  = self.getCoordSpaceTransform()

        if xform is not None:

            lohi = transform.transform([lo, hi], xform)
            lohi.sort(axis=0)
            lo, hi = lohi[0, :], lohi[1, :]

        self.bounds = [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]]
            
    
    def __overlayListChanged(self, *a):
        """Called when the overlay list changes. Updates the :attr:`refImage`
        property so that it contains a list of overlays which can be
        associated with the model.
        """
        
        imgProp  = self.getProp('refImage')
        imgVal   = self.refImage
        overlays = self.displayCtx.getOrderedOverlays()

        # the overlay for this ModelOpts
        # instance has been removed
        if self.overlay not in overlays:
            self.overlayList.removeListener('overlays', self.name)
            return

        imgOptions = [None]

        for overlay in overlays:
            
            # The overlay must be an Image instance.
            if not isinstance(overlay, fslimage.Image):
                continue

            imgOptions.append(overlay)
                
            overlay.addListener('name',
                                self.name,
                                self.__overlayListChanged,
                                overwrite=True)
            
        imgProp.setChoices(imgOptions, instance=self)

        if imgVal in overlays: self.refImage = imgVal
        else:                  self.refImage = None
