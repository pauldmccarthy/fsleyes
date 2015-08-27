#!/usr/bin/env python
#
# displaycontext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import logging

import props

import display as fsldisplay


log = logging.getLogger(__name__)


class InvalidOverlayError(Exception):
    """An error raised by the :meth:`DisplayContext.getDisplay`
    and :meth:`DisplayContext.getOpts` methods to indicate that
    the specified overlay is not in the :class:`.OverlayList`.
    """
    pass


class DisplayContext(props.SyncableHasProperties):
    """Contains a number of properties defining how an :class:`.OverlayList`
    is to be displayed.
    """

    
    selectedOverlay = props.Int(minval=0, default=0, clamped=True)
    """Index of the currently 'selected' overlay.

    Note that this index is in relation to the
    :class:`.OverlayList`, rather than to the :attr:`overlayOrder`
    list.

    If you're interested in the currently selected overlay, you must also
    listen for changes to the :attr:`.OverlayList.images` list as, if the list
    changes, the :attr:`selectedOverlay` index may not change, but the overlay
    to which it points may be different.
    """


    location = props.Point(ndims=3)
    """The location property contains the currently selected
    3D location (xyz) in the current display coordinate system.
    """

    
    bounds = props.Bounds(ndims=3)
    """This property contains the min/max values of a bounding box (in display
    coordinates) which is big enough to contain all of the overlays in the
    :attr:`overlays` list. This property shouid be read-only, but I don't have
    a way to enforce it (yet).
    """


    overlayOrder = props.List(props.Int())
    """A list of indices into the :attr:`.OverlayList.overlays`
    list, defining the order in which the overlays are to be displayed.

    See the :meth:`getOrderedOverlays` method.
    """


    overlayGroups = props.List()
    """A list of :class:`.OverlayGroup` instances, each of which defines
    a group of overlays which share display properties.
    """


    syncOverlayDisplay = props.Boolean(default=True)
    """If this ``DisplayContext`` instance has a parent (see
    :mod:`props.syncable`), and this is ``True``, the properties of the
    :class:`.Display` and :class:`.DisplayOpts`  for every overlay managed
     by this ``DisplayContext`` instance will be synchronised to those of
    the parent instance. Otherwise, the display properties for every overlay
    will be unsynchronised from the parent.

    This property is accessed by the :class:`.Display` class, in its
    :meth:`.Display.__init__` method, and when it creates new
    :class:`.DisplayOpts` instances, to set initial sync states.
    """


    def __init__(self, overlayList, parent=None):
        """Create a :class:`DisplayContext` object.

        :arg overlayList: A :class:`.OverlayList` instance.

        :arg parent: Another :class`DisplayContext` instance to be used
        as the parent of this instance.
        """

        props.SyncableHasProperties.__init__(
            self,
            parent=parent,
            nounbind=['overlayGroups'],
            nobind=[  'syncOverlayDisplay'])

        self.__overlayList = overlayList
        self.__name         = '{}_{}'.format(self.__class__.__name__, id(self))

        # Keep track of the overlay list
        # length so we can do some things in the
        # _overlayListChanged method. This if/else
        # is a bit hacky ....
        #
        # If the __overlayListChanged method detects
        # (via the prevOverlayListLen attribute)
        # that overlays have been added to an empty
        # list, it will reset the DisplayContext.location
        # to the centre of the new overlay list world.
        #
        # But, if this is a new child DisplayContext
        # instance, the above behaviour will result in
        # the child centering its location, which gets
        # propagated back to the parent, clobbering the
        # parent's location. So here, if this is a child
        # DC, we set this attribute to the length of the
        # list, so the overlayListChanged method won't
        # reset the location.
        if parent is None: self.__prevOverlayListLen = 0
        else:              self.__prevOverlayListLen = len(overlayList)
            

        # Ensure that a Display object exists
        # for every overlay, and that the display
        # bounds property is initialised
        self.__displays = {}
        self.__overlayListChanged()
        
        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)

        self.addListener('syncOverlayDisplay',
                         self.__name,
                         self.__syncOverlayDisplayChanged)

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))

        
    def __del__(self):
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

        
    def destroy(self):

        self.__overlayList.removeListener('overlays', self.__name)

        for overlay, display in self.__displays.items():
            display.destroy()

        self.__displays = None

        
    def getDisplay(self, overlay, overlayType=None):
        """Returns the display property object (e.g. a :class:`.Display`
        object) for the specified overlay (or overlay index).

        If a :class:`Display` object does not exist for the given overlay,
        one is created.

        :arg overlay:     The overlay to retrieve a ``Display``
                          instance for.

        :arg overlayType: If a ``Display`` instance for the specified
                          ``overlay`` does not exist, one is created - the
                          specified ``overlayType`` is passed to the
                          :meth:`.Display.__init__` method.
        """

        if overlay is None:
            raise ValueError('No overlay specified')

        if overlay not in self.__overlayList:
            raise InvalidOverlayError('Overlay {} is not in '
                                      'list'.format(overlay.name))

        if isinstance(overlay, int):
            overlay = self.__overlayList[overlay]

        try:
            display = self.__displays[overlay]
                
        except KeyError:
                
            if self.getParent() is None:
                dParent = None
            else:
                dParent = self.getParent().getDisplay(overlay, overlayType)
                if overlayType is None:
                    overlayType = dParent.overlayType
                
            display = fsldisplay.Display(overlay,
                                         self.__overlayList,
                                         self,
                                         parent=dParent,
                                         overlayType=overlayType)
            self.__displays[overlay] = display
        
        return display


    def getOpts(self, overlay, overlayType=None):
        """Returns the :class:`.DisplayOpts` instance associated with the
        specified overlay.

        See :meth:`.Display.getDisplayOpts` and :meth:`getDisplay`. 
        """

        if overlay is None:
            raise ValueError('No overlay specified')

        if overlay not in self.__overlayList:
            raise InvalidOverlayError('Overlay {} is not in '
                                      'list'.format(overlay.name)) 

        return self.getDisplay(overlay, overlayType).getDisplayOpts()


    def getReferenceImage(self, overlay):
        """Convenience method which returns the reference image associated
        with the given overlay, or ``None`` if there is no reference image.

        See the :class:`.DisplayOpts.getReferenceImage` method.
        """
        if overlay is None:
            return None
        
        return self.getOpts(overlay).getReferenceImage()

        
    def selectOverlay(self, overlay):
        """Selects the specified ``overlay``. Raises an ``IndexError`` if
        the overlay is not in the list.
        """
        self.selectedOverlay = self.__overlayList.index(overlay)

    
    def getSelectedOverlay(self):
        """Returns the currently selected overlay object,
        or ``None`` if there are no overlays.
        """
        if len(self.__overlayList) == 0: return None
        return self.__overlayList[self.selectedOverlay]

    
    def getOverlayOrder(self, overlay):
        """Returns the order in which the given overlay (or an index into
        the :class:`.OverlayList` list) should be displayed
        (see the :attr:`overlayOrder property).

        Raises an ``IndexError`` if the overlay is not in the list.
        """
        self.__syncOverlayOrder()
        
        if not isinstance(overlay, int):
            overlay = self.__overlayList.index(overlay)
            
        return self.overlayOrder.index(overlay)

    
    def getOrderedOverlays(self):
        """Returns a list of overlay objects from
        the :class:`.OverlayList` list, sorted into the order
        that they are to be displayed.
        """
        self.__syncOverlayOrder()
        return [self.__overlayList[idx] for idx in self.overlayOrder]


    def __overlayListChanged(self, *a):
        """Called when the :attr:`.OverlayList.overlays` property
        changes.

        Ensures that a :class:`.Display` and :class:`.DisplayOpts` object
        exists for every image, updates the :attr:`bounds` property, makes
        sure that the :attr:`overlayOrder` property is consistent, and updates
        constraints on the :attr:`selectedOverlay` property.
        """

        # Discard all Display instances
        # which refer to overlays that
        # are no longer in the list
        for overlay in list(self.__displays.keys()):
            if overlay not in self.__overlayList:
                
                display = self.__displays.pop(overlay)
                opts    = display.getDisplayOpts()

                display.removeListener('overlayType', self.__name)
                opts   .removeListener('bounds',      self.__name)
                
                # The display instance will destroy the
                # opts instance, so we don't do it here
                display.destroy()
 
        # Ensure that a Display object
        # exists for every overlay in
        # the list
        for overlay in self.__overlayList:

            # The getDisplay method
            # will create a Display object
            # if one does not already exist
            display = self.getDisplay(overlay)
            opts    = display.getDisplayOpts()

            # Register a listener on the overlay type,
            # because when it changes, the DisplayOpts
            # instance will change, and we will need to
            # re-register the next listener
            display.addListener('overlayType',
                                self.__name,
                                self.__overlayListChanged,
                                overwrite=True)

            # Register a listener on the DisplayOpts
            # object for every overlay - if any
            # DisplayOpts properties change, the
            # overlay display bounds may have changed,
            # so we need to know when this happens.
            opts.addListener('bounds',
                             self.__name,
                             self.__overlayBoundsChanged,
                             overwrite=True)

        # Ensure that the overlayOrder
        # property is valid
        self.__syncOverlayOrder()

        # Ensure that the bounds property is accurate
        self.__updateBounds()

        # If the overlay list was empty,
        # and is now non-empty, centre
        # the currently selected location
        if (self.__prevOverlayListLen == 0) and (len(self.__overlayList) > 0):
            
            # initialise the location to be
            # the centre of the world
            b = self.bounds
            self.location.xyz = [
                b.xlo + b.xlen / 2.0,
                b.ylo + b.ylen / 2.0,
                b.zlo + b.zlen / 2.0]
            
        self.__prevOverlayListLen = len(self.__overlayList)
 
        # Limit the selectedOverlay property
        # so it cannot take a value greater
        # than len(overlayList)-1
        nOverlays = len(self.__overlayList)
        if nOverlays > 0:
            self.setConstraint('selectedOverlay', 'maxval', nOverlays - 1)
        else:
            self.setConstraint('selectedOverlay', 'maxval', 0)


    def __syncOverlayOrder(self):
        """Ensures that the :attr:`overlayOrder` property is up to date
        with respect to the :class:`.OverlayList`.
        """

        if len(self.overlayOrder) == len(self.__overlayList):
            return

        #
        # NOTE: The following logic assumes that operations
        #       which modify the overlay list will only do
        #       one of the following:
        #
        #        - Adding one or more overlays to the list
        #        - Removing one or more overlays from the list
        # 
        # More complex overlay list modifications
        # will cause this code to break.

        oldList  = self.__overlayList.getLastValue('overlays')[:]
        oldOrder = self.overlayOrder[:]

        # If the overlay order was just the
        # list order, preserve that ordering
        if self.overlayOrder[:] == range(len(oldList)):
            self.overlayOrder[:] = range(len(self.__overlayList))
        
        # If overlays have been added to
        # the overlay list, add indices
        # for them to the overlayOrder list
        elif len(self.overlayOrder) < len(self.__overlayList):
            
            newOrder      = []
            newOverlayIdx = len(oldList)

            # The order of existing overlays is preserved,
            # and all new overlays added to the end of the
            # overlay order. 
            for overlay in self.__overlayList:

                if overlay in oldList:
                    newOrder.append(oldOrder[oldList.index(overlay)])
                else:
                    newOrder.append(newOverlayIdx)
                    newOverlayIdx += 1

            self.overlayOrder[:] = newOrder

        # Otherwise, if overlays have been 
        # removed from the overlay list ...
        elif len(self.overlayOrder) > len(self.__overlayList):

            # Remove the corresponding indices
            # from the overlayOrder list
            for i, overlay in enumerate(oldList):
                if overlay not in self.__overlayList:
                    oldOrder.remove(i)

            # Re-generate new indices,
            # preserving the order of
            # the remaining overlays
            newOrder = [sorted(oldOrder).index(idx) for idx in oldOrder]
            self.overlayOrder[:] = newOrder

            
    def __overlayBoundsChanged(self, value, valid, opts, name):
        """Called when the :attr:`.DisplayOpts.bounds` property of any
        overlay changes. Updates the :attr:`bounds` property and preserves
        the display :attr:`location` in terms of hte currently selected
        overlay.
        """

        # This check is ugly, and is required due to
        # an ugly circular relationship which exists
        # between parent/child DCs and the *Opts/
        # location properties:
        # 
        # 1. When a property of a child DC DisplayOpts
        #    object changes (e.g. ImageOpts.transform)
        #    this should always be due to user input),
        #    that change is propagated to the parent DC
        #    DisplayOpts object.
        #
        # 2. This results in the DC._displayOptsChanged
        #    method (this method) being called on the
        #    parent DC.
        #
        # 3. Said method correctly updates the DC.location
        #    property, so that the world location of the
        #    selected overlay is preserved.
        #
        # 4. This location update is propagated back to
        #    the child DC.location property, which is
        #    updated to have the new correct location
        #    value.
        #
        # 5. Then, the child DC._displayOpteChanged method
        #    is called, which goes and updates the child
        #    DC.location property to contain a bogus
        #    value.
        #
        # So this test is in place to prevent this horrible
        # circular loop behaviour from occurring. If the
        # location properties are synced, and contain the
        # same value, we assume that they don't need to be
        # updated again, and escape from ths system.
        if self.getParent() is not None and self.isSyncedToParent('location'):
            return

        overlay = opts.display.getOverlay()

        # Save a copy of the location before
        # updating the bounds, as the change
        # to the bounds may result in the
        # location being modified
        oldDispLoc = self.location.xyz

        # Update the display context bounds
        # to take into account any changes 
        # to individual overlay bounds
        self.disableNotification('location')
        self.__updateBounds()
        self.enableNotification('location')
 
        # The main purpose of this method is to preserve
        # the current display location in terms of the
        # currently selected overlay, when the overlay
        # bounds have changed. We don't care about changes
        # to the options for other overlays.
        if (overlay != self.getSelectedOverlay()):
            self.notify('location')
            return

        # Now we want to update the display location
        # so that it is preserved with respect to the
        # currently selected overlay.
        newDispLoc = opts.transformDisplayLocation(oldDispLoc)

        # Ignore the new display location
        # if it is not in the display bounds
        if self.bounds.inBounds(newDispLoc):
            log.debug('Preserving display location in '
                      'terms of overlay {} ({}.{}): {} -> {}'.format(
                          overlay,
                          type(opts).__name__,
                          name,
                          oldDispLoc,
                          newDispLoc))

            self.location.xyz = newDispLoc
        else:
            self.notify('location')


    def __syncOverlayDisplayChanged(self, *a):
        """Called when the :attr:`syncOverlayDisplay` property
        changes.

        Synchronises or unsychronises the :class:`.Display` and
        :class:`.DisplayOpts` instances for every overlay to/from their
        parent instances.
        """

        if self.getParent() is None:
            return

        for display in self.__displays.values():
            
            opts = display.getDisplayOpts()

            if self.syncOverlayDisplay:
                display.syncAllToParent()
                opts   .syncAllToParent()
            else:
                display.unsyncAllFromParent()
                opts   .unsyncAllFromParent()

                
    def __updateBounds(self, *a):
        """Called when the overlay list changes, or when any overlay display
        transform is changed. Updates the :attr:`bounds` property.
        """

        if len(self.__overlayList) == 0:
            minBounds = [0.0, 0.0, 0.0]
            maxBounds = [0.0, 0.0, 0.0]
            
        else:
            minBounds = 3 * [ sys.float_info.max]
            maxBounds = 3 * [-sys.float_info.max]

        for ovl in self.__overlayList:

            display = self.__displays[ovl]
            opts    = display.getDisplayOpts()
            lo      = opts.bounds.getLo()
            hi      = opts.bounds.getHi()

            for ax in range(3):

                if lo[ax] < minBounds[ax]: minBounds[ax] = lo[ax]
                if hi[ax] > maxBounds[ax]: maxBounds[ax] = hi[ax]

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]]
        
        # Update the constraints on the :attr:`location` 
        # property to be aligned with the new bounds
        self.location.setLimits(0, self.bounds.xlo, self.bounds.xhi)
        self.location.setLimits(1, self.bounds.ylo, self.bounds.yhi)
        self.location.setLimits(2, self.bounds.zlo, self.bounds.zhi)
