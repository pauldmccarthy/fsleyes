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
import contextlib

import numpy        as np
import numpy.linalg as npla

import        fsl.data.image as fslimage
import        fsleyes_props  as props
from . import group          as dcgroup


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
        displayToWorld
        worldToDisplay
        displaySpaceIsRadiological
        selectOverlay
        getSelectedOverlay
        getOverlayOrder
        getOrderedOverlays
        freeze
        freezeOverlay
        thawOverlay
        defaultDisplaySpace
        detachDisplaySpace
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
    in the display coordinate system. Different ``DisplayContext`` instances
    may be using different display coordinate systems - see the
    :attr:`displaySpace` property.
    """


    worldLocation = props.Point(ndims=3)
    """The :attr:`location` property contains the currently selected 3D
    location (xyz) in the current display coordinate system. Whenever the
    :attr:`location` changes, it gets transformed into the world coordinate
    system, and propagated to this property. The location of different
    ``DisplayContext`` instances is synchronised through this property.

    .. note:: If any :attr:`.NiftiOpts.transform` properties have been modified
              independently of the :attr:`displaySpace`, this value will be
              invalid.
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

    By default there is one overlay group, to which all new overlays are
    initially added. The :class:`.OverlayListPanel` allows the user to
    add/remove overlays from this default group.
    """


    syncOverlayDisplay = props.Boolean(default=True)
    """If this ``DisplayContext`` instance has a parent (see
    :mod:`props.syncable`), and this property is ``True``, the properties of
    the :class:`.Display` and :class:`.DisplayOpts` instances for every
    overlay managed by this ``DisplayContext`` instance will be synchronised
    to those of the parent instance. Otherwise, the display properties for
    every overlay will be unsynchronised from the parent.

    Properties which control the current volume/timepoint in a 4D data set are
    not managed by this property - see the :attr: :attr:`syncOverlayVolume`
    property.

    Synchronisation of the following properties between child and parent
    ``DisplayContext`` instances is also controlled by this flag:

      - :attr:`displaySpace`
      - :attr:`bounds`
      - :attr:`radioOrientation`

    .. note:: This property is accessed by the :class:`.Display` class, in its
              constructor, and when it creates new :class:`.DisplayOpts`
              instances, to set initial sync states.
    """


    syncOverlayVolume = props.Boolean(default=True)
    """This property performs the same task as the :attr:`syncOverlayDisplay`
    property, but it only affects :class:`DisplayOpts` properties which control
    the current volume/timepoint in a 4D overlay.
    """


    displaySpace = props.Choice(('world', ))
    """The *space* in which overlays are displayed. This property defines the
    display coordinate system for this ``DisplayContext``. When it is changed,
    the :attr:`.NiftiOpts.transform` property of all :class:`.Nifti` overlays
    in the :class:`.OverlayList` is updated. It has two settings, described
    below. The options for this property are dynamically added by
    :meth:`__updateDisplaySpaceOptions`.

    1. **World** space (a.k.a. ``'world'``)

       All :class:`.Nifti` overlays are displayed in the space defined by
       their affine transformation matrix - the :attr:`.NiftiOpts.transform`
       property for every ``Nifti`` overlay is set to ``affine``.

    2. **Reference image** space

       A single :class:`.Nifti` overlay is selected as a *reference* image,
       and is displayed in scaled voxel space (with a potential L/R flip for
       neurological images - its :attr:`.NiftiOpts.transform` is set to
       ``pixdim-flip``). All other ``Nifti`` overlays are transformed into
       this reference space - their :attr:`.NiftiOpts.transform` property is
       set to ``reference``, which results in them being transformed into the
       scaled voxel space of the reference image.

    .. note:: The :attr:`.NiftiOpts.transform` property of any
              :class:`.Nifti` overlay can be set independently of this
              property. However, whenever *this* property changes, it will
              change the ``transform`` property for every ``Nifti``, in the
              manner described above.

    The :meth:`defaultDisplaySpace` can be used to control how the
    ``displaySpace`` is initialised.
    """


    radioOrientation = props.Boolean(default=True)
    """If ``True``, 2D views will show images in radiological convention
    (i.e.subject left on the right of the display). Otherwise, they will be
    shown in neurological convention (subject left on the left).

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


    def __init__(self, overlayList, parent=None, defaultDs='ref', **kwargs):
        """Create a ``DisplayContext``.

        :arg overlayList: An :class:`.OverlayList` instance.

        :arg parent:      Another ``DisplayContext`` instance to be used
                          as the parent of this instance, passed to the
                          :class:`.SyncableHasProperties` constructor.

        :arg defaultDs:   Initial value for the :meth:`defaultDisplaySpace`.
                          Either ``'ref'`` or ``'world'``. If ``'ref'`` (the
                          default), when overlays are added to an empty list,
                          the :attr:`displaySpace` will be set to the first
                          :class:`.Nifti` overlay. Otherwise (``'world'``),
                          the display space will be set to ``'world'``.

        All other arguments are passed through to the ``SyncableHasProperties``
        constructor, in addition to the following:

          - The ``syncOverlayDisplay``,, ``syncOverlayVolume``, ``location``,
            and ``bounds`` properties are added to the ``nobind`` argument

          - The ``overlayGroups``, ``autoDisplay`` and ``loadInMemory``
            properties are added to the ``nounbind`` argument.
        """

        kwargs = dict(kwargs)

        nobind   = kwargs.pop('nobind',   [])
        nounbind = kwargs.pop('nounbind', [])

        nobind  .extend(['syncOverlayDisplay',
                         'syncOverlayVolume',
                         'location',
                         'bounds'])
        nounbind.extend(['overlayGroups',
                         'autoDisplay',
                         'loadInMemory'])

        kwargs['parent']   = parent
        kwargs['nobind']   = nobind
        kwargs['nounbind'] = nounbind
        kwargs['state']    = {'overlayOrder' : False}

        props.SyncableHasProperties.__init__(self, **kwargs)

        self.__overlayList = overlayList
        self.__name        = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__child       = parent is not None

        # When the first overlay(s) is/are
        # added, the display space may get
        # set either to a reference image,
        # or to world. The defaultDisplaySpace
        # controls this behaviour.
        self.defaultDisplaySpace = defaultDs

        # The overlayOrder is unsynced by
        # default, but we will inherit the
        # current parent value.
        if self.__child: self.overlayOrder[:] = parent.overlayOrder[:]
        else:            self.overlayOrder[:] = range(len(overlayList))

        # If this is the first child DC, we
        # need to initialise the display
        # space and location. If there is
        # already a child DC, then we have
        # (probably) inherited initial
        # settings.
        if self.__child:
            self.__initDS = (len(parent.getChildren()) - 1) == 0


        # While the DisplayContext may refer to
        # multiple overlay groups, we are currently
        # using just one, allowing the user to specify
        # a set of overlays for which their display
        # properties are 'locked'.
        if not self.__child:
            lockGroup = dcgroup.OverlayGroup(self, overlayList)
            self.overlayGroups.append(lockGroup)

        # This dict contains the Display
        # objects for every overlay in
        # the overlay list, as
        # {Overlay : Display} mappings
        self.__displays = {}

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged,
                                immediate=True)

        if self.__child:
            self.addListener('syncOverlayDisplay',
                             self.__name,
                             self.__syncOverlayDisplayChanged)
            self.addListener('syncOverlayVolume',
                             self.__name,
                             self.__syncOverlayVolumeChanged)
            self.addListener('displaySpace',
                             self.__name,
                             self.__displaySpaceChanged,
                             immediate=True)
            self.addListener('location',
                             self.__name,
                             self.__locationChanged,
                             immediate=True)
            self.addListener('worldLocation',
                             self.__name,
                             self.__worldLocationChanged,
                             immediate=True)

        # The overlayListChanged method
        # is important - check it out
        self.__overlayListChanged()

        log.debug('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""

        # The log atribute, and internals of the
        # logging module, be GC'd before this
        # method is called, so absorb any errors.
        try:
            log.debug('%s.del (%s)', type(self).__name__, id(self))
        except Exception:
            pass


    def destroy(self):
        """This method must be called when this ``DisplayContext`` is no
        longer needed.

        When a ``DisplayContext`` is destroyed, all of the :class:`.Display`
        instances managed by it are destroyed as well.
        """

        self.detachAllFromParent()

        overlayList = self.__overlayList
        displays    = self.__displays

        self.__overlayList = None
        self.__displays    = None

        overlayList.removeListener('overlays', self.__name)

        if self.__child:
            self.removeListener('syncOverlayDisplay', self.__name)
            self.removeListener('syncOverlayVolume',  self.__name)
            self.removeListener('displaySpace',       self.__name)
            self.removeListener('location',           self.__name)
            self.removeListener('worldLocation',      self.__name)
        else:
            for g in list(self.overlayGroups):
                self.overlayGroups.remove(g)
                g.destroy()

        for overlay, display in displays.items():
            display.destroy()


    @property
    def destroyed(self):
        """Returns ``True`` if this ``DisplayContext`` has been, or is being,
        destroyed, ``False`` otherwise.
        """
        return self.__overlayList is None


    def getDisplay(self, overlay, **kwargs):
        """Returns the :class:`.Display` instance for the specified overlay
        (or overlay index).

        If the overlay is not in the ``OverlayList``, an
        :exc:`InvalidOverlayError` is raised.  Otheriwse, if a
        :class:`Display` object does not exist for the given overlay, one is
        created.

        If this ``DisplayContext`` has been destroyed, a ``ValueError`` is
        raised.

        :arg overlay:     The overlay to retrieve a ``Display`` instance for,
                          or an index into the ``OverlayList``.

        All other keyword arguments are assumed to be ``name=value`` pairs,
        containing initial property values.
        """

        if overlay is None:
            raise ValueError('No overlay specified')

        if self.destroyed:
            raise ValueError('DisplayContext has been destroyed')

        if overlay not in self.__overlayList:
            raise InvalidOverlayError('Overlay {} is not in '
                                      'list'.format(overlay.name))

        if isinstance(overlay, int):
            overlay = self.__overlayList[overlay]

        try:
            display = self.__displays[overlay]

        except KeyError:

            if not self.__child:
                dParent = None
            else:
                dParent = self.getParent().getDisplay(overlay, **kwargs)

            from .display import Display

            display = Display(overlay,
                              self.__overlayList,
                              self,
                              parent=dParent,
                              **kwargs)
            self.__displays[overlay] = display

        return display


    def getOpts(self, overlay):
        """Returns the :class:`.DisplayOpts` instance associated with the
        specified overlay.  See :meth:`getDisplay` and :meth:`.Display.opts`
        for more details.
        """

        if overlay is None:
            raise ValueError('No overlay specified')

        if self.destroyed:
            raise ValueError('DisplayContext has been destroyed')

        if overlay not in self.__overlayList:
            raise InvalidOverlayError('Overlay {} is not in '
                                      'list'.format(overlay.name))

        return self.getDisplay(overlay).opts


    def getReferenceImage(self, overlay):
        """Convenience method which returns the reference image associated
        with the given overlay, or ``None`` if there is no reference image.

        See the :class:`.DisplayOpts.referenceImage` method.
        """
        if overlay is None:
            return None

        return self.getOpts(overlay).referenceImage


    def displayToWorld(self, dloc, *args, **kwargs):
        """Transforms the given coordinates from the display coordinate
        system into the world coordinate system.

        .. warning:: If any :attr:`.NiftiOpts.transform` properties have
                     been modified manually, this method will return invalid
                     results.

        All other arguments are passed to the
        :meth:`.NiftiOpts.transformCoords` method.
        """

        displaySpace = self.displaySpace

        if displaySpace == 'world' or len(self.__overlayList) == 0:
            return dloc

        opts = self.getOpts(displaySpace)

        return opts.transformCoords(dloc, 'display', 'world', *args, **kwargs)


    def worldToDisplay(self, wloc, *args, **kwargs):
        """Transforms the given coordinates from the world coordinate
        system into the display coordinate system.

        .. warning:: If any :attr:`.NiftiOpts.transform` properties have
                     been modified manually, this method will return invalid
                     results.

        All other arguments are passed to the
        :meth:`.NiftiOpts.transformCoords` method.
        """

        displaySpace = self.displaySpace

        if displaySpace == 'world' or len(self.__overlayList) == 0:
            return wloc

        opts = self.getOpts(displaySpace)

        return opts.transformCoords(wloc, 'world', 'display', *args, **kwargs)


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
        if self.__child:
            self.getParent().freezeOverlay(overlay)
            return

        dctxs = [self] + self.getChildren()

        for dctx in dctxs:
            display = dctx.getDisplay(overlay)
            opts    = display.opts

            display.disableAllNotification()
            opts   .disableAllNotification()


    def thawOverlay(self, overlay):
        """Enables notification for all :class:`.Display` and
        :class:`.DisplayOpts` properties associated with the given ``overlay``.
        """

        if self.__child:
            self.getParent().thawOverlay(overlay)
            return
        dctxs = [self] + self.getChildren()

        for dctx in dctxs:
            display = dctx.getDisplay(overlay)
            opts    = display.opts

            display.enableAllNotification()
            opts   .enableAllNotification()


    @property
    def defaultDisplaySpace(self):
        """This property controls how the :attr:`displaySpace` is initialised
        when overlays are added to a previously empty :class:`.OverlayList`.
        If the ``defaultDisplaySpace`` is set to ``'ref'``, the
        ``displaySpace`` will be initialised to the first :class:`.Nifti`
        overlay. Otherwise (the ``defaultDisplaySpace`` is set to ``'world'``),
        the ``displaySpace`` will be set to ``'world'``.
        """
        return self.__defaultDisplaySpace


    @defaultDisplaySpace.setter
    def defaultDisplaySpace(self, ds):
        """Sets the :meth:`defaultDisplaySpace`.

        :arg ds: Either ``'ref'`` or ``'world'``.
        """
        if ds not in ('world', 'ref'):
            raise ValueError('Invalid default display space: {}'.format(ds))
        self.__defaultDisplaySpace = ds


    def detachDisplaySpace(self):
        """Detaches the :attr:`displaySpace` and :attr:`bounds` properties,
        and all related :class:`.DisplayOpts` properties, from the parent
        ``DisplayContext``.

        This allows this ``DisplayContext`` to use a display coordinate
        system that is completely independent from other instances, and is not
        affected by changes to the parent properties.

        This is an irreversible operation.
        """

        self.detachFromParent('displaySpace')
        self.detachFromParent('bounds')

        for ovl in self.__overlayList:

            opts = self.getOpts(ovl)

            opts.detachFromParent('bounds')

            if isinstance(ovl, fslimage.Nifti):
                opts.detachFromParent('transform')


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
                opts    = display.opts

                display.removeListener('overlayType', self.__name)
                opts   .removeListener('bounds',      self.__name)

                # The display instance will destroy the
                # opts instance, so we don't do it here
                display.destroy()

        # Ensure that a Display object exists
        # for every overlay in the list
        for overlay in self.__overlayList:

            initProps = self.__overlayList.initProps(overlay)

            # The getDisplay method
            # will create a Display object
            # if one does not already exist
            new     = overlay not in self.__displays
            display = self.getDisplay(overlay, **initProps)
            opts    = display.opts

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
            # update our own bounds property. This is only
            # done on child DCs, as the parent DC bounds
            # only gets used for synchronisation
            if self.__child:
                opts.addListener('bounds',
                                 self.__name,
                                 self.__overlayBoundsChanged,
                                 overwrite=True)

                # If detachDisplaySpace has been called,
                # make sure the opts bounds (and related)
                # properties are also detached
                if not self.canBeSyncedToParent('displaySpace'):
                    opts.detachFromParent('bounds')
                    if isinstance(overlay, fslimage.Nifti):
                        opts.detachFromParent('transform')

            # All new overlays are initially
            # added to the default overlay group.
            # This only needs to be done on the
            # master DC, as the overlayGroups are
            # the same across all DCs.
            if new and not self.__child and len(self.overlayGroups) > 0:
                self.overlayGroups[0].addOverlay(overlay)

        # Ensure that the displaySpace
        # property options are in sync
        # with the overlay list.
        self.__updateDisplaySpaceOptions()

        # The rest of the stuff only
        # needs to be done on child DCs
        if not self.__child:
            return

        # Limit the selectedOverlay property
        # so it cannot take a value greater
        # than len(overlayList)-1. selectedOverlay
        # is always synchronised, so we only
        # need to do this on the parent DC.
        nOverlays = len(self.__overlayList)
        if nOverlays > 0:
            self.setAttribute('selectedOverlay',
                              'maxval',
                              nOverlays - 1)
        else:
            self.setAttribute('selectedOverlay', 'maxval', 0)

        # Ensure that the overlayOrder
        # property is valid
        self.__syncOverlayOrder()

        # If the overlay list was empty,
        # and is now non-empty, we need
        # to initialise the display space
        # and the display location
        initDS        = self.__initDS                      and \
                        np.all(np.isclose(self.bounds, 0)) and \
                        len(self.__overlayList) > 0
        self.__initDS = len(self.__overlayList) == 0

        # Initialise the display space. We
        # have to do this before updating
        # image transforms, and updating
        # the display bounds
        if initDS:

            displaySpace = 'world'

            if self.defaultDisplaySpace == 'ref':
                for overlay in self.__overlayList:
                    if isinstance(overlay, fslimage.Nifti):
                        displaySpace = overlay
                        break

            with props.skip(self, 'displaySpace', self.__name):
                self.displaySpace = displaySpace

        # Initialise the transform property
        # of any Image overlays which have
        # just been added to the list,
        oldList = self.__overlayList.getLastValue('overlays')[:]
        for overlay in self.__overlayList:
            if isinstance(overlay, fslimage.Nifti) and \
               (overlay not in oldList):
                self.__setTransform(overlay)

        # Ensure that the bounds
        # property is accurate
        self.__updateBounds()

        # Initialise the display location to
        # the centre of the display bounds
        if initDS:
            b = self.bounds
            self.location.xyz = [
                b.xlo + b.xlen / 2.0,
                b.ylo + b.ylen / 2.0,
                b.zlo + b.zlen / 2.0]
            self.__propagateLocation('world')
        else:
            self.__propagateLocation('display')


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

        choiceProp.setChoices(choices, instance=self)


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
        # method does not get called. Use
        # ignoreInvalid, because this method might
        # get called before we have registered a
        # listener on the bounds property.
        with props.skip(opts, 'bounds', self.__name, ignoreInvalid=True):
            if   space == 'world':  opts.transform = 'affine'
            elif image is space:    opts.transform = 'pixdim-flip'
            else:                   opts.transform = 'reference'


    def __displaySpaceChanged(self, *a):
        """Called when the :attr:`displaySpace` property changes. Updates the
        :attr:`.NiftiOpts.transform` property for all :class:`.Nifti`
        overlays in the :class:`.OverlayList`.
        """

        selectedOverlay = self.getSelectedOverlay()

        if selectedOverlay is None:
            return

        # Update the transform property of all
        # Image overlays to put them into the
        # new display space
        for overlay in self.__overlayList:

            if not isinstance(overlay, fslimage.Nifti):
                continue

            self.__setTransform(overlay)

        # Update the display world bounds,
        # and then update the location
        self.__updateBounds()

        # Make sure that the location is
        # kept in the same place, relative
        # to the world coordinate system
        self.__propagateLocation('display')


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
        elif len(oldList) < len(self.__overlayList):

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
        elif len(oldList) > len(self.__overlayList):

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
        the display :attr:`location` in terms of the :attr:`worldLocation`.
        """

        # This method might get called
        # after DisplayOpts instance
        # has been destroyed
        if opts.display is None:
            return

        # Update the display context bounds
        # to take into account any changes
        # to individual overlay bounds.
        # Inhibit notification on the location
        # property - it will be updated properly
        # below
        self.__updateBounds()

        # Make sure the display location
        # is consistent w.r.t. the world
        # coordinate location
        self.__propagateLocation('display')


    def __syncOverlayDisplayChanged(self, *a):
        """Called when the :attr:`syncOverlayDisplay` property
        changes.

        Synchronises or unsychronises the :class:`.Display` and
        :class:`.DisplayOpts` instances for every overlay to/from their
        parent instances.
        """

        dcProps = ['displaySpace', 'bounds', 'radioOrientation']

        if self.syncOverlayDisplay:
            for p in dcProps:
                if self.canBeSyncedToParent(p):
                    self.syncToParent(p)

        else:
            for p in dcProps:
                if self.canBeUnsyncedFromParent(p):
                    self.unsyncFromParent(p)

        for display in self.__displays.values():

            if self.syncOverlayDisplay:
                display.syncAllToParent()
            else:
                display.unsyncAllFromParent()

            opts     = display.opts
            optProps = opts.getAllProperties()[0]
            exclude  = opts.getVolumeProps()

            for optProp in optProps:

                # volume properties are managed
                # by syncOverlayVolume
                if optProp in exclude:
                    continue

                if self.syncOverlayDisplay:
                    if opts.canBeSyncedToParent(optProp):
                        opts.syncToParent(optProp)
                else:
                    if opts.canBeUnsyncedFromParent(optProp):
                        opts.unsyncFromParent(optProp)


    def __syncOverlayVolumeChanged(self, *a):
        """Called when the :attr:`syncOverlayVolume` property changes.

        Synchronises or unsychronises the volume/timepoint properties of
        the :class:`.Display` and :class:`.DisplayOpts` instances for every
        overlay.
        """

        for display in self.__displays.values():
            opts     = display.opts
            optProps = opts.getVolumeProps()

            for optProp in optProps:
                if self.syncOverlayVolume:
                    if opts.canBeSyncedToParent(optProp):
                        opts.syncToParent(optProp)
                else:
                    if opts.canBeUnsyncedFromParent(optProp):
                        opts.unsyncFromParent(optProp)


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
            opts    = display.opts
            lo      = opts.bounds.getLo()
            hi      = opts.bounds.getHi()

            for ax in range(3):

                if lo[ax] < minBounds[ax]: minBounds[ax] = lo[ax]
                if hi[ax] > maxBounds[ax]: maxBounds[ax] = hi[ax]

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]]

        # Update the constraints on the location
        # property to be aligned with the new bounds
        with props.suppress(self, 'location'):
            self.location.setLimits(0, self.bounds.xlo, self.bounds.xhi)
            self.location.setLimits(1, self.bounds.ylo, self.bounds.yhi)
            self.location.setLimits(2, self.bounds.zlo, self.bounds.zhi)


    def __locationChanged(self, *a):
        """Called when the :attr:`location` property changes. Propagates
        the new location to the :attr:`worldLocation` property.
        """
        self.__propagateLocation('world')


    def __worldLocationChanged(self, *a):
        """Called when the :attr:`worldLocation` property changes. Propagates
        the new location to the :attr:`location` property.
        """

        self.__propagateLocation('display')


    def __propagateLocation(self, dest):
        """Called by the :meth:`__locationChanged` and
        :meth:`__worldLocationChanged` methods. The ``dest`` argument may be
        either ``'world'`` (the ``worldLocation`` is updated from the
        ``location``), or ``'display'`` (vice-versa).
        """

        if self.displaySpace == 'world':
            if dest == 'world':
                with props.skip(self, 'worldLocation', self.__name):
                    self.worldLocation = self.location
            else:
                with props.skip(self, 'location', self.__name):
                    self.location = self.worldLocation
            return

        ref  = self.displaySpace
        opts = self.getOpts(ref)

        if dest == 'world':
            with props.skip(self, 'location', self.__name):
                self.worldLocation = opts.transformCoords(
                    self.location, 'display', 'world')
        else:
            with props.skip(self, 'worldLocation', self.__name):
                self.location = opts.transformCoords(
                    self.worldLocation, 'world', 'display')
