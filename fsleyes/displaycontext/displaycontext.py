#!/usr/bin/env python
#
# displaycontext.py - The DisplayContext class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`DisplayContext` class, which defines
general display settings for displaying the overlays in a
:class:`.OverlayList`.
"""


import sys
import logging
import weakref
import contextlib

import numpy        as np
import numpy.linalg as npla

import fsl.data.image      as fslimage
import fsl.utils.transform as transform
import fsleyes_props       as props


log = logging.getLogger(__name__)


class InvalidOverlayError(Exception):
    """An error raised by the :meth:`DisplayContext.getDisplay`
    and :meth:`DisplayContext.getOpts` methods to indicate that
    the specified overlay is not in the :class:`.OverlayList`.
    """
    pass


class DisplayContext(props.SyncableHasProperties):
    """A ``DisplayContext`` instance contains a number of properties defining
    how the overlays in an :class:`.OverlayList` are to be displayed, and
    related contextual information.


    A ``DisplayContext`` instance is responsible for creating and destroying
    :class:`.Display` instances for every overlay in the
    ``OverlayList``. These ``Display`` instances, and the corresponding
    :class:`.DisplayOpts` instances (which, in turn, are created/destroyed by
    ``Display`` instances) can be accessed with the :meth:`getDisplay` and
    :meth:`getOpts` method respectively.


    A number of other useful methods are provided by a ``DisplayContext``
    instance:

    .. autosummary::
       :nosignatures:

        getDisplay
        getOpts
        getReferenceImage
        selectOverlay
        getSelectedOverlay
        getOverlayOrder
        getOrderedOverlays
        cacheStandardCoordinates
    """


    selectedOverlay = props.Int(minval=0, default=0, clamped=True)
    """Index of the currently 'selected' overlay.

    .. note:: The value of this index is in relation to the
              :class:`.OverlayList`, rather than to the :attr:`overlayOrder`
              list.

              If you're interested in the currently selected overlay, you must
              also listen for changes to the :attr:`.OverlayList.images` list
              as, if the list changes, the :attr:`selectedOverlay` index may
              not change, but the overlay to which it points may be different.
    """


    location = props.Point(ndims=3)
    """The location property contains the currently selected 3D location (xyz)
    in the display coordinate system.
    """


    bounds = props.Bounds(ndims=3)
    """This property contains the min/max values of a bounding box (in display
    coordinates) which is big enough to contain all of the overlays in the
    :class:`.OverlayList`.

    .. warning:: This property shouid be treated as read-only.
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
    :mod:`props.syncable`), and this property is ``True``, the properties of
    the :class:`.Display` and :class:`.DisplayOpts` instances for every
    overlay managed by this ``DisplayContext`` instance will be synchronised
    to those of the parent instance. Otherwise, the display properties for
    every overlay will be unsynchronised from the parent.

    .. note:: This property is accessed by the :class:`.Display` class, in its
              constructor, and when it creates new :class:`.DisplayOpts`
              instances, to set initial sync states.
    """


    displaySpace = props.Choice(('world', ))
    """The *space* in which overlays are displayed. This property globally
    controls the :attr:`.NiftiOpts.transform` property of all :class:`.Nifti`
    overlays. It has two settings, described below. The options for this
    property are dynamically added by :meth:`__updateDisplaySpaceOptions`.

    1. **World** space (a.k.a. ``'world'``)

       All :class:`.Nifti` overlays are displayed in the space defined by
       their affine transformation matrix - the :attr:`.NiftiOpts.transform`
       property for every ``Nifti`` overlay is set to ``affine``.

    2. **Reference image** space

       A single :class:`.Nifti` overlay is selected as a *reference* image,
       and is displayed in scaled voxel space (with a potential L/R flip for
       neurological images - :attr:`.NiftiOpts.transform` is set to
       ``pixdim-flip``). All other ``Nifti`` overlays are transformed into
       this reference space - their :attr:`.NiftiOpts.transform` property is
       set to ``custom``, and their :attr:`.NiftiOpts.customXform` matrix is
       set such that it transforms from the image voxel space to the scaled
       voxel space of the reference image.

    .. note:: The :attr:`.NiftiOpts.transform` property of any
              :class:`.Nifti` overlay can be set independently of this
              property. However, whenever *this* property changes, it will
              change the ``transform`` property for every ``Nifti``, in the
              manner described above.
    """


    radioOrientation = props.Boolean(default=True)
    """If ``True``, 2D views will show images in radiological convention
    (i.e.subject left on the right of the display). Otherwise, they will be
    shown  in neurological convention (subject left on the left).

    .. note:: This setting is not enforced by the ``DisplayContext``. It is
              the responsibility of the :class:`.OrthoPanel` and
              :class:`.LightBoxPanel` (and other potential future 2D view
              panels) to implement the flip.
    """


    autoDisplay = props.Boolean(default=False)
    """If ``True``, whenever an overlay is added to the :class:`.OverlayList`,
    the :mod:`autodisplay` module will be used to automatically configure
    its display settings. Note that the ``DisplayContext`` does not perform
    this configuration - this flag is used by other modules (e.g. the
    :class:`.OverlayListPanel` and the :class:`.OpenFileAction`).
    """


    loadInMemory = props.Boolean(default=False)
    """If ``True``, all :class:`.Image` instances will be loaded into memory,
    regardless of their size. Otherwise (the default), large compressed
    ``Image`` overlays may be kept on disk.


    .. note:: Changing the value of this property will not affect existing
              ``Image`` overlays.


    .. note:: This property may end up being used in a more general sense by
              any code which needs to decide whether to do things in a more
              or less memory-intensive manner.
    """


    def __init__(self, overlayList, parent=None):
        """Create a ``DisplayContext``.

        :arg overlayList: An :class:`.OverlayList` instance.

        :arg parent:      Another ``DisplayContext`` instance to be used
                          as the parent of this instance, passed to the
                          :class:`.SyncableHasProperties` constructor.
        """

        props.SyncableHasProperties.__init__(
            self,
            parent=parent,
            nounbind=['selectedOverlay',
                      'overlayGroups',
                      'displaySpace',
                      'radioOrientation',
                      'bounds',
                      'autoDisplay',
                      'loadInMemory'],
            nobind=[  'syncOverlayDisplay'],
            state={'overlayOrder' : False})

        self.__overlayList = overlayList
        self.__name        = '{}_{}'.format(self.__class__.__name__, id(self))

        # The overlayOrder is unsynced by
        # default, but we will inherit the
        # current parent value. If this
        # DC is a parent, the overlayOrder
        # will be initialised in the call
        # to __syncOverlayOrder, below.
        if parent is not None:
            self.overlayOrder[:] = parent.overlayOrder[:]

        # Keep track of the overlay list length so
        # we can do some things in the
        # __overlayListChanged method. This if/else
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

        # This dict contains the Display objects for
        # every overlay in the overlay list, as
        # {Overlay : Display} mappings
        self.__displays = {}

        # We keep a cache of 'standard' coordinates,
        # one for each overlay - see the cacheStandardCoordinates
        # method.  We're storing this cache in a tricky
        # way though - as an attribute of the location
        # property. We do this so that the cache will be
        # automatically synchronised between parent/child
        # DC objects.
        locPropVal = self.getPropVal('location')

        # Only set the standardCoords cache if
        # it has not already been set (if this
        # is a child DC, the cache will have
        # already been set on the parent)
        try:
            locPropVal.getAttribute('standardCoords')
        except KeyError:
            locPropVal.setAttribute('standardCoords',
                                    weakref.WeakKeyDictionary())

        # The overlayListChanged and displaySpaceChanged
        # methods do important things - check them out
        self.__overlayListChanged()
        self.__displaySpaceChanged()

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged,
                                immediate=True)

        self.addListener('syncOverlayDisplay',
                         self.__name,
                         self.__syncOverlayDisplayChanged)
        self.addListener('displaySpace',
                         self.__name,
                         self.__displaySpaceChanged,
                         immediate=True)

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.memory('{}.del ({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """This method must be called when this ``DisplayContext`` is no
        longer needed.

        When a ``DisplayContext`` is destroyed, all of the :class:`.Display`
        instances managed by it are destroyed as well.
        """

        self.detachFromParent()

        self.__overlayList.removeListener('overlays',           self.__name)
        self              .removeListener('syncOverlayDisplay', self.__name)
        self              .removeListener('displaySpace',       self.__name)

        for overlay, display in self.__displays.items():
            display.destroy()

        self.__displays = None


    def getDisplay(self, overlay, overlayType=None):
        """Returns the :class:`.Display` instance for the specified overlay
        (or overlay index).

        If the overlay is not in the ``OverlayList``, an
        :exc:`InvalidOverlayError` is raised.  Otheriwse, if a
        :class:`Display` object does not exist for the given overlay, one is
        created.

        :arg overlay:     The overlay to retrieve a ``Display`` instance for,
                          or an index into the ``OverlayList``.

        :arg overlayType: If a ``Display`` instance for the specified
                          ``overlay`` does not exist, one is created - in
                          this case, the specified ``overlayType`` is passed
                          to the :class:`.Display` constructor.
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

            from .display import Display

            display = Display(overlay,
                              self.__overlayList,
                              self,
                              parent=dParent,
                              overlayType=overlayType)
            self.__displays[overlay] = display

        return display


    def getOpts(self, overlay, overlayType=None):
        """Returns the :class:`.DisplayOpts` instance associated with the
        specified overlay.  See :meth:`getDisplay` and
        :meth:`.Display.getDisplayOpts` for more details,
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


    def displaySpaceIsRadiological(self):
        """Returns ``True`` if the current :attr:`displaySpace` aligns with
        a radiological orientation. A radiological orientation is one in
        which anatomical right is shown on the left of the screen, i.e.:

          - The X axis corresponds to right -> left
          - The Y axis corresponds to posterior -> anterior
          - The Z axis corresponds to inferior -> superior
        """

        if len(self.__overlayList) == 0:
            return True

        space = self.displaySpace

        # Display space is either 'world', or an image.
        # We assume that 'world' is an RAS coordinate
        # system which, if transferred directly to a
        # display coordinate system, would result in a
        # neurological view (left on left, right on
        # right).
        if space == 'world':
            return False
        else:
            opts  = self.getOpts(space)
            xform = opts.getTransform('pixdim-flip', 'display')

            return npla.det(xform) > 0


    def selectOverlay(self, overlay):
        """Selects the specified ``overlay``. Raises an :exc:`IndexError` if
        the overlay is not in the list.

        If you want to select an overlay by its index in the ``OverlayList``,
        you can just assign to the :attr:`selectedOverlay` property directly.
        """
        self.selectedOverlay = self.__overlayList.index(overlay)


    def getSelectedOverlay(self):
        """Returns the currently selected overlay object,
        or ``None`` if there are no overlays.
        """
        if len(self.__overlayList) == 0:                    return None
        if self.selectedOverlay >= len(self.__overlayList): return None

        return self.__overlayList[self.selectedOverlay]


    def getOverlayOrder(self, overlay):
        """Returns the order in which the given overlay (or an index into
        the :class:`.OverlayList` list) should be displayed
        (see the :attr:`overlayOrder` property).

        Raises an :exc:`IndexError` if the overlay is not in the list.
        """
        self.__syncOverlayOrder()

        if not isinstance(overlay, int):
            overlay = self.__overlayList.index(overlay)

        return self.overlayOrder.index(overlay)


    def getOrderedOverlays(self):
        """Returns a list of overlay objects from the :class:`.OverlayList`
        list, sorted into the order that they should be displayed, as defined
        by the :attr:`overlayOrder` property.
        """
        self.__syncOverlayOrder()

        return [self.__overlayList[idx] for idx in self.overlayOrder]


    def cacheStandardCoordinates(self, overlay, coords):
        """Stores the given _standard_ coordinates for the given overlay.

        This method must be called by :class:`.DisplayOpts` sub-classes
        whenever the spatial representation of their overlay changes -
        ``DisplayOpts`` instances need to transform the current display
        :attr:`location` into a consistent coordinate system, relative to
        their overlay.

        This is necessary in order for the ``DisplayContext`` to update the
        :attr:`location` with respect to the currently selected overlay - if
        the current overlay has shifted in the display coordinate system, we
        want the :attr:`location` to shift with it.

        :arg overlay: The overlay object (e.g. an :class:`.Image`).

        :arg coords:  Coordinates in the standard coordinate system of the
                      overlay.
        """

        if self.getParent() is not None and self.isSyncedToParent('location'):
            return

        locPropVal     = self.getPropVal('location')
        standardCoords = weakref.WeakKeyDictionary(
            locPropVal.getAttribute('standardCoords'))

        standardCoords[overlay] = np.array(coords).tolist()

        locPropVal.setAttribute('standardCoords', standardCoords)

        log.debug('Standard coordinates cached '
                  'for overlay {}: {} <-> {}'.format(
                      overlay.name,
                      self.location.xyz,
                      coords))


    @contextlib.contextmanager
    def freeze(self, overlay):
        """This method can be used as a context manager to suppress
        notification for all :class:`.Display` and :class:`.DisplayOpts`
        properties related to the given ``overlay``::

            with displayCtx.freeze(overlay):
                # Do stuff which might trigger unwanted
                # Display/DisplayOpts notifications

        See :meth:`freezeOverlay` and :meth:`thawOverlay`.
        """
        self.freezeOverlay(overlay)

        try:
            yield

        finally:
            self.thawOverlay(overlay)


    def freezeOverlay(self, overlay):
        """Suppresses notification for all :class:`.Display` and
        :class:`.DisplayOpts` properties associated with the given ``overlay``.
        Call :meth:`.thawOverlay` to re-enable notification.

        See also the :meth:`freeze` method, which can be used as a context
        manager to automatically call this method and ``thawOverlay``.
        """
        parent = self.getParent()
        if parent is not None:
            parent.freezeOverlay(overlay)
            return

        dctxs = [self] + self.getChildren()

        for dctx in dctxs:
            display = dctx.getDisplay(overlay)
            opts    = display.getDisplayOpts()

            display.disableAllNotification()
            opts   .disableAllNotification()


    def thawOverlay(self, overlay):
        """Enables notification for all :class:`.Display` and
        :class:`.DisplayOpts` properties associated with the given ``overlay``.
        """

        parent = self.getParent()
        if parent is not None:
            parent.thawOverlay(overlay)
            return
        dctxs = [self] + self.getChildren()

        for dctx in dctxs:
            display = dctx.getDisplay(overlay)
            opts    = display.getDisplayOpts()

            display.enableAllNotification()
            opts   .enableAllNotification()


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

        # Ensure that a Display object exists
        # for every overlay in the list
        for overlay in self.__overlayList:

            ovlType = self.__overlayList.initOverlayType(overlay)

            # The getDisplay method
            # will create a Display object
            # if one does not already exist
            display = self.getDisplay(overlay, ovlType)
            opts    = display.getDisplayOpts()

            # Register a listener on the overlay type,
            # because when it changes, the DisplayOpts
            # instance will change, and we will need
            # to re-register the DisplayOpts.bounds
            # listener (see the next statement)
            display.addListener('overlayType',
                                self.__name,
                                self.__overlayListChanged,
                                overwrite=True)

            # Register a listener on the DisplayOpts.bounds
            # property for every overlay - if the display
            # bounds for any overlay changes, we need to
            # update our own bounds property.
            opts.addListener('bounds',
                             self.__name,
                             self.__overlayBoundsChanged,
                             overwrite=True)

        # Ensure that the overlayOrder
        # property is valid
        self.__syncOverlayOrder()

        # Ensure that the bounds
        # property is accurate
        self.__updateBounds()

        # Ensure that the displaySpace
        # property options are in sync
        # with the overlay list
        self.__updateDisplaySpaceOptions()

        # Initliase the transform property
        # of any Image overlays which have
        # just been added to the list,
        oldList  = self.__overlayList.getLastValue('overlays')[:]
        for overlay in self.__overlayList:
            if isinstance(overlay, fslimage.Nifti) and \
               (overlay not in oldList):
                self.__setTransform(overlay)

        # If the overlay list was empty,
        # and is now non-empty ...
        if (self.__prevOverlayListLen == 0) and (len(self.__overlayList) > 0):

            # Set the displaySpace to
            # the first new image
            for overlay in self.__overlayList:
                if isinstance(overlay, fslimage.Nifti):
                    self.displaySpace = overlay
                    break

            # Centre the currently selected
            # location (but see the comments
            # in __init__ about this).
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


    def __updateDisplaySpaceOptions(self):
        """Updates the :attr:`displaySpace` property so it is synchronised with
        the current contents of the :class:`.OverlayList`

        This method is called by the :meth:`__overlayListChanged` method.
        """

        choiceProp = self.getProp('displaySpace')
        choices    = []

        for overlay in self.__overlayList:
            if isinstance(overlay, fslimage.Nifti):
                choices.append(overlay)

        choices.append('world')

        choiceProp.setChoices(choices,    instance=self)
        choiceProp.setDefault(choices[0], instance=self)


    def __setTransform(self, image):
        """Sets the :attr:`.NiftiOpts.transform` property associated with
        the given :class:`.Nifti` overlay to a sensible value, given the
        current value of the :attr:`.displaySpace` property.

        Called by the :meth:`__displaySpaceChanged` method, and by
        :meth:`__overlayListChanged` for any :class:`.Image` overlays which
        have been newly added to the :class:`.OverlayList`.

        :arg image: An :class:`.Image` overlay.
        """

        space = self.displaySpace
        opts  = self.getOpts(image)

        # Disable notification of the bounds
        # property so the __overlayBoundsChanged
        # method does not get called.
        opts.disableListener('bounds', self.__name)

        if   space == 'world':  opts.transform = 'affine'
        elif image is space:    opts.transform = 'pixdim-flip'
        else:
            refOpts = self.getOpts(space)
            xform   = transform.concat(
                refOpts.getTransform('world', 'pixdim-flip'),
                opts   .getTransform('voxel', 'world'))

            opts.customXform = xform
            opts.transform   = 'custom'

        opts.enableListener('bounds', self.__name)


    def __displaySpaceChanged(self, *a):
        """Called when the :attr:`displaySpace` property changes. Updates the
        :attr:`.NiftiOpts.transform` property for all :class:`.Nifti`
        overlays in the :class:`.OverlayList`.
        """

        # If this DC is synced to a parent, let the
        # parent do the update - our location property
        # will be automatically synced to it. If we
        # don't do this check, we will clobber the
        # parent's updated location (or vice versa)
        if self.getParent() is not None and self.isSyncedToParent('location'):
            return

        selectedOverlay = self.getSelectedOverlay()

        if selectedOverlay is None:
            return

        selectedOpts = self.getOpts(selectedOverlay)

        # The transform of the currently selected
        # overlay might change, so we want the
        # location to be preserved with respect to it.
        stdLoc = selectedOpts.displayToStandardCoordinates(self.location.xyz)

        # Update the transform property of all
        # Image overlays to put them into the
        # new display space
        for overlay in self.__overlayList:

            if not isinstance(overlay, fslimage.Nifti):
                continue

            self.__setTransform(overlay)

        # Update the display world bounds,
        # and then update the location
        with props.suppress(self, 'location'):
            self.__updateBounds()

        # making sure that the location is kept
        # in the same place, relative to the
        # currently selected overlay
        self.location.xyz = selectedOpts.standardToDisplayCoordinates(stdLoc)


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
        #        - Adding one or more overlays to the end of the list
        #        - Removing one or more overlays from the list
        #
        # More complex overlay list modifications
        # will cause this code to break.

        oldList  = self.__overlayList.getLastValue('overlays')[:]
        oldOrder = self.overlayOrder[:]

        # If the overlay order was just the
        # list order, preserve that ordering
        if self.overlayOrder[:] == list(range(len(oldList))):
            self.overlayOrder[:] = list(range(len(self.__overlayList)))

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
        the display :attr:`location` in terms of the currently selected
        overlay.
        """

        # See the note at top of __displaySpaceChanged
        # method regarding this test
        if self.getParent() is not None and self.isSyncedToParent('location'):
            return

        # This method might get called
        # after DisplayOpts instance
        # has been destroyed
        if opts.display is None:
            return

        overlay = opts.display.getOverlay()

        # If the bounds of an overlay have changed, the
        # overlay might have been moved in the dispaly
        # coordinate system. We want to keep the
        # current location in the same position, relative
        # to that overlay. So we get the cached standard
        # coords (which should have been updated by the
        # overlay's DisplayOpts instance - see the docs
        # for the cacheStandardCoordinates), and use them
        # below to restore the location
        locPropVal = self.getPropVal('location')
        stdLoc     = locPropVal.getAttribute('standardCoords')[overlay]

        # Update the display context bounds
        # to take into account any changes
        # to individual overlay bounds.
        # Inhibit notification on the location
        # property - it will be updated properly
        # below
        with props.suppress(self, 'location'):
            self.__updateBounds()

        # The main purpose of this method is to preserve
        # the current display location in terms of the
        # currently selected overlay, when the overlay
        # bounds have changed. We don't care about changes
        # to the options for other overlays.
        if overlay != self.getSelectedOverlay():
            self.propNotify('location')
            return

        # Now we want to update the display location
        # so that it is preserved with respect to the
        # currently selected overlay.
        newDispLoc = opts.standardToDisplayCoordinates(stdLoc)

        # Ignore the new display location
        # if it is not in the display bounds
        if self.bounds.inBounds(newDispLoc):
            log.debug('Preserving display location in '
                      'terms of overlay {} ({}.{}): {} -> {}'.format(
                          overlay,
                          type(opts).__name__,
                          name,
                          stdLoc,
                          newDispLoc))

            self.location.xyz = newDispLoc
        else:
            self.propNotify('location')


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
        transform is changed. Updates the :attr:`bounds` property so that it
        is big enough to contain all of the overlays (as defined by their
        :attr:`.DisplayOpts.bounds` properties).
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
