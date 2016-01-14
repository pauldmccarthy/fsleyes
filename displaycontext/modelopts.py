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
    """If ``True``, the model name is shown alongside the model.

    .. note:: Not implemented yet.
    """

    
    refImage = props.Choice()
    """A reference :class:`.Image` instance which the model coordinates are
    in terms of.

    For example, if this :class:`.Model` represents the segmentation of a
    sub-cortical region from a T1 image, you would set the ``refImage`` to that
    T1 image.

    Any :class:`.Image` instance in the :class:`.OverlayList` may be chosen
    as the reference image.
    """


    coordSpace = copy.copy(volumeopts.Nifti1Opts.transform)
    """If :attr:`refImage` is not ``None``, this property defines the
    reference image coordinate space in which the model coordinates are
    defined (i.e. voxels, scaled voxels, or world coordinates).
    """


    def __init__(self, *args, **kwargs):
        """Create a ``ModelOpts`` instance. All arguments are passed through
        to the :class:`.DisplayOpts` constructor.
        """

        # The Nifti1Opts.transform property has a
        # 'custom' option which is not applicable
        # to our coordSpace property.
        coordSpace = self.getProp('coordSpace')
        coordSpace.removeChoice('custom', self)

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

        self.addListener('refImage',
                         self.name,
                         self.__refImageChanged,
                         immediate=True)
        self.addListener('coordSpace',
                         self.name,
                         self.__coordSpaceChanged,
                         immediate=True)
        
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

        if self.refImage is not None and \
           self.refImage in self.overlayList:
            opts = self.displayCtx.getOpts(self.refImage)
            opts.removeListener('transform',   self.name)
            opts.removeListener('customXform', self.name)
                
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

        if self.refImage is None:
            return None

        opts = self.displayCtx.getOpts(self.refImage)

        return opts.getTransform(self.coordSpace, opts.transform)
    

    def displayToStandardCoordinates(self, coords):
        """Transforms the given coordinates into a standardised coordinate
        system specific to the overlay associated with this ``ModelOpts``
        instance.

        The coordinate system used is the coordinate system in which the
        :class:`.Model` vertices are defined.
        """
        if self.refImage is None:
            return coords

        opts = self.displayCtx.getOpts(self.refImage)
        
        return opts.transformCoords(coords, opts.transform, self.coordSpace)

    
    def standardToDisplayCoordinates(self, coords):
        """Transforms the given coordinates from standardised coordinates
        into the display coordinate system - see
        :meth:`displayToStandardCoordinates`.
        """
        if self.refImage is None:
            return coords

        opts = self.displayCtx.getOpts(self.refImage)
        
        return opts.transformCoords(coords, self.coordSpace, opts.transform)

    
    def __cacheCoords(self,
                      refImage=-1,
                      coordSpace=None,
                      transform=None,
                      customXform=None):
        """Caches the current :attr:`.DisplayContext.location` in standardised
        coordinates see the :meth:`.DisplayContext.cacheStandardCoordinates`
        method).

        This method is called whenever the :attr:`refImage` or
        :attr:`coordSpace` properties change and, if a ``refImage`` is
        specified, whenever the :attr:`.Nifti1Opts.transform` or
        :attr:`.Nifti1Opts.customXform` properties change.

        :arg refImage:    Reference image to use to calculate the coordinates.
                          If ``-1`` the :attr:`refImage` is used (``-1`` is
                          used as the default value instead of ``None`` because
                          the latter is a valid value for ``refImage``).
        
        :arg coordSpace:  Coordinate space value to use - if ``None``, the
                          :attr:`coordSpace` is used.
        
        :arg transform:   Transform to use - if ``None``, and a ``refImage`` is
                          defined, the :attr:`.Nifti1Opts.transform` value is
                          used.
        
        :arg customXform: Custom transform to use (if
                          ``transform=custom``). If ``None``, and a
                          ``refImage`` is defined, the
                          :attr:`.Nifti1Opts.customXform` value is used.
        """

        if refImage   is -1:   refImage   = self.refImage
        if coordSpace is None: coordSpace = self.coordSpace

        if refImage is None:
            coords = self.displayCtx.location.xyz
            
        else:
            refOpts = self.displayCtx.getOpts(refImage)

            if transform   is None: transform   = refOpts.transform
            if customXform is None: customXform = refOpts.customXform

            # TODO if transform == custom, we 
            # have to use the old custom xform
            
            coords  = refOpts.transformCoords(self.displayCtx.location.xyz,
                                              transform,
                                              coordSpace)
        
        self.displayCtx.cacheStandardCoordinates(self.overlay, coords)


    def __transformChanged(self, value, valid, ctx, name):
        """Called when the :attr:`.Nifti1Opts.transfrom` or
        :attr:`.Nifti1Opts.customXform` properties of the current
        :attr:`refImage` change. Calls :meth:`__updateBounds`.
        """

        refOpts = ctx

        if   name == 'transform':
            transform   = refOpts.getLastValue('transform')
            customXform = refOpts.customXform
        elif name == 'customXform': 
            transform   = refOpts.transform
            customXform = refOpts.getLastValue('customXform')

        self.__cacheCoords(transform=transform, customXform=customXform)
        self.__updateBounds()


    def __coordSpaceChanged(self, *a):
        """Called when the :attr:`coordSpace` property changes.
        Calls :meth:`__updateBounds`.
        """

        oldValue = self.getLastValue('coordSpace')

        if oldValue is None:
            oldValue = self.coordSpace

        self.__cacheCoords(coordSpace=oldValue)
        self.__updateBounds()


    def __refImageChanged(self, *a):
        """Called when the :attr:`refImage` property changes.

        If a new reference image has been specified, removes listeners from
        the old one (if necessary), and adds listeners to the
        :attr:`.Nifti1Opts.transform` and :attr:`.Nifti1Opts.customXform`
        properties associated with the new image. Calls
        :meth:`__updateBounds`.
        """
        
        oldValue = self.getLastValue('refImage')

        self.__cacheCoords(refImage=oldValue) 

        # TODO You are not tracking changes to the
        # refImage overlay type -  if this changes,
        # you will need to re-bind to the transform
        # property of the new DisplayOpts instance

        if self.__oldRefImage is not None and \
           self.__oldRefImage in self.overlayList:
            
            opts = self.displayCtx.getOpts(self.__oldRefImage)
            opts.removeListener('transform',   self.name)
            opts.removeListener('customXform', self.name)

        self.__oldRefImage = self.refImage

        if self.refImage is not None:
            opts = self.displayCtx.getOpts(self.refImage)
            opts.addListener('transform',
                             self.name,
                             self.__transformChanged,
                             immediate=True)
            opts.addListener('customXform',
                             self.name,
                             self.__transformChanged,
                             immediate=True)

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

            # The overlay must be a Nifti1 instance.
            if not isinstance(overlay, fslimage.Nifti1):
                continue

            imgOptions.append(overlay)

            display = self.displayCtx.getDisplay(overlay)
            display.addListener('name',
                                self.name,
                                self.__overlayListChanged,
                                overwrite=True)
            
        imgProp.setChoices(imgOptions, instance=self)

        if imgVal in overlays: self.refImage = imgVal
        else:                  self.refImage = None
