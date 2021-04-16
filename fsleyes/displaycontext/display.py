#!/usr/bin/env python
#
# display.py - Definitions of the Display and DisplayOpts classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Display` and :class:`DisplayOpts` classes,
which encapsulate overlay display settings.
"""


import logging
import inspect

import fsl.data.image                 as fslimage
import fsl.data.constants             as constants
import fsleyes_props                  as props
import fsleyes_widgets.utils.typedict as td

import fsleyes.strings                as strings
import fsleyes.actions                as actions


log = logging.getLogger(__name__)


class Display(props.SyncableHasProperties):
    """The ``Display`` class contains display settings which are common to
    all overlay types.

    A ``Display`` instance is also responsible for managing a single
    :class:`DisplayOpts` instance, which contains overlay type specific
    display options. Whenever the :attr:`overlayType` property of a
    ``Display`` instance changes, the old ``DisplayOpts`` instance (if any)
    is destroyed, and a new one, of the correct type, created.
    """


    name = props.String()
    """The overlay name. """


    overlayType = props.Choice()
    """This property defines the overlay type - how the data is to be
    displayed.

    The options for this property are populated in the :meth:`__init__`
    method, from the :attr:`.displaycontext.OVERLAY_TYPES` dictionary. A
    :class:`DisplayOpts` sub-class exists for every possible value that this
    property may take.

    """

    enabled = props.Boolean(default=True)
    """Should this overlay be displayed at all? """


    alpha = props.Percentage(default=100.0)
    """Opacity - 100% is fully opaque, and 0% is fully transparent."""


    brightness = props.Percentage()
    """Brightness - 50% is normal brightness."""


    contrast   = props.Percentage()
    """Contrast - 50% is normal contrast."""


    def __init__(self,
                 overlay,
                 overlayList,
                 displayCtx,
                 parent=None,
                 **kwa):
        """Create a :class:`Display` for the specified overlay.

        :arg overlay:     The overlay object.

        :arg overlayList: The :class:`.OverlayList` instance which contains
                          all overlays.

        :arg displayCtx:  A :class:`.DisplayContext` instance describing how
                          the overlays are to be displayed.

        :arg parent:      A parent ``Display`` instance - see
                          :mod:`props.syncable`.

        All other keyword arguments are assumed to be ``name=value`` pairs,
        containing initial property values, for both this ``Display``, and
        the initially created :class:`DisplayOpts` instance. For the latter,
        it is assumed that any properties specified are appropriate for the
        initial overlay type.
        """

        dispProps     = self.getAllProperties()[0]
        initDispProps = {n : v for n, v in kwa.items() if n     in dispProps}
        initOptProps  = {n : v for n, v in kwa.items() if n not in dispProps}

        self.__overlay     = overlay
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.name          = overlay.name

        # Populate the possible choices
        # for the overlayType property
        from . import getOverlayTypes

        ovlTypes    = getOverlayTypes(overlay)
        ovlTypeProp = self.getProp('overlayType')

        log.debug('Enabling overlay types for {}: '.format(overlay, ovlTypes))
        ovlTypeProp.setChoices(ovlTypes, instance=self)

        # Call the super constructor after our own
        # initialisation, in case the provided parent
        # has different property values to our own,
        # and our values need to be updated
        props.SyncableHasProperties.__init__(
            self,
            parent=parent,

            # These properties cannot be unbound, as
            # they affect the OpenGL representation.
            # The name can't be unbound either,
            # because it would be silly to allow
            # different names for the same overlay.
            nounbind=['overlayType', 'name'],

            # Initial sync state between this
            # Display and the parent Display
            # (if this Display has a parent)
            state=displayCtx.syncOverlayDisplay,

            # set initial display property values
            **initDispProps)

        # When the overlay type changes, the property
        # values of the DisplayOpts instance for the
        # old overlay type are stored in this dict.
        # If the overlay is later changed back to the
        # old type, its previous values are restored.
        #
        # The structure of the dictionary is:
        #
        #   { (type(DisplayOpts), propName) : propValue }
        #
        # This also applies to the case where the
        # overlay type is changed from one type to
        # a related type (e.g. from VolumeOpts to
        # LabelOpts) - the values of all common
        # properties are copied to the new
        # DisplayOpts instance.
        self.__oldOptProps = td.TypeDict()

        # Initial DisplayOpt property values
        # are used in the first call to
        # __makeDisplayOpts, and then cleared
        # afterwards.
        self.__initOptProps = initOptProps

        # Set up listeners after caling Syncable.__init__,
        # so the callbacks don't get called during
        # synchronisation
        self.addListener(
            'overlayType',
            'Display_{}'.format(id(self)),
            self.__overlayTypeChanged)

        # The __overlayTypeChanged method creates
        # a new DisplayOpts instance - for this,
        # it needs to be able to access this
        # Display instance's parent (so it can
        # subsequently access a parent for the
        # new DisplayOpts instance). Therefore,
        # we do this after calling Syncable.__init__.
        self.__displayOpts = None
        self.__overlayTypeChanged()

        log.debug('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.debug('{}.del ({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """This method must be called when this ``Display`` instance
        is no longer needed.

        When a ``Display`` instance is destroyed, the corresponding
        :class:`DisplayOpts` instance is also destroyed.
        """

        if self.__displayOpts is not None:
            self.__displayOpts.destroy()

        self.removeListener('overlayType', 'Display_{}'.format(id(self)))

        self.detachAllFromParent()

        self.__oldOptProps  = None
        self.__initOptProps = None
        self.__displayOpts  = None
        self.__overlayList  = None
        self.__displayCtx   = None
        self.__overlay      = None


    @property
    def overlay(self):
        """Returns the overlay associated with this ``Display`` instance."""
        return self.__overlay


    @property
    def opts(self):
        """Return the :class:`.DisplayOpts` instance associated with this
        ``Display``, which contains overlay type specific display settings.

        If a ``DisplayOpts`` instance has not yet been created, or the
        :attr:`overlayType` property no longer matches the type of the
        existing ``DisplayOpts`` instance, a new ``DisplayOpts`` instance
        is created (and the old one destroyed if necessary).

        See the :meth:`__makeDisplayOpts` method.
        """

        if (self.__displayOpts             is None) or \
           (self.__displayOpts.overlayType != self.overlayType):

            if self.__displayOpts is not None:
                self.__displayOpts.destroy()

            self.__displayOpts = self.__makeDisplayOpts()

        return self.__displayOpts


    def __makeDisplayOpts(self):
        """Creates a new :class:`DisplayOpts` instance. The specific
        ``DisplayOpts`` sub-class that is created is dictated by the current
        value of the :attr:`overlayType` property.

        The :data:`.displaycontext.DISPLAY_OPTS_MAP` dictionary defines the
        mapping between overlay types and :attr:`overlayType` values, and
        ``DisplayOpts`` sub-class types.
        """

        if self.getParent() is None:
            oParent = None
        else:
            oParent = self.getParent().opts

        initOptProps        = self.__initOptProps
        self.__initOptProps = None

        if initOptProps is None:
            initOptProps = {}

        from . import DISPLAY_OPTS_MAP

        optType = DISPLAY_OPTS_MAP[self.__overlay, self.overlayType]

        log.debug('Creating {} instance (synced: {}) for overlay '
                  '{} ({})'.format(optType.__name__,
                                   self.__displayCtx.syncOverlayDisplay,
                                   self.__overlay, self.overlayType))

        volProps  = optType.getVolumeProps()
        allProps  = optType.getAllProperties()[0]
        initState = {}

        for p in allProps:
            if p in volProps:
                initState[p] = self.__displayCtx.syncOverlayVolume
            else:
                initState[p] = self.__displayCtx.syncOverlayDisplay

        return optType(self.__overlay,
                       self,
                       self.__overlayList,
                       self.__displayCtx,
                       parent=oParent,
                       state=initState,
                       **initOptProps)


    def __findOptBaseType(self, optType, optName):
        """Finds the class, in the hierarchy of the given ``optType`` (a
        :class:`.DisplayOpts` sub-class) in which the given ``optName``
        is defined.

        This method is used by the :meth:`__saveOldDisplayOpts` method, and
        is an annoying necessity caused by the way that the :class:`.TypeDict`
        class works. A ``TypeDict`` does not allow types to be used as keys -
        they must be strings containing the type names.

        Furthermore, in order for the property values of a common
        ``DisplayOpts`` base type to be shared across sub types (e.g. copying
        the :attr:`.NiftiOpts.transform` property between :class:`.VolumeOpts`
        and :class:`.LabelOpts` instances), we need to store the name of the
        common base type in the dictionary.
        """

        for base in inspect.getmro(optType):
            if optName in base.__dict__:
                return base

        return None


    def __saveOldDisplayOpts(self):
        """Saves the value of every property on the current
        :class:`DisplayOpts` instance, so they can be restored later if
        needed.
        """

        opts = self.__displayOpts

        if opts is None:
            return

        for propName in opts.getAllProperties()[0]:
            base = self.__findOptBaseType(type(opts), propName)
            base = base.__name__
            val  = getattr(opts, propName)

            log.debug('Saving {}.{} = {} [{} {}]'.format(
                base, propName, val, type(opts).__name__, id(self)))

            self.__oldOptProps[base, propName] = val


    def __restoreOldDisplayOpts(self):
        """Restores any cached values for all of the properties on the
        current :class:`DisplayOpts` instance.
        """
        opts = self.__displayOpts

        if opts is None:
            return

        for propName in opts.getAllProperties()[0]:

            try:
                value = self.__oldOptProps[opts, propName]

                if not hasattr(opts, propName):
                    continue

                if not opts.propertyIsEnabled(propName):
                    continue

                log.debug('Restoring {}.{} = {} [{}]'.format(
                    type(opts).__name__, propName, value, id(self)))

                setattr(opts, propName, value)

            except KeyError:
                pass


    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`overlayType` property changes. Makes sure
        that the :class:`DisplayOpts` instance is of the correct type.
        """
        self.__saveOldDisplayOpts()
        self.opts
        self.__restoreOldDisplayOpts()


class DisplayOpts(props.SyncableHasProperties, actions.ActionProvider):
    """The ``DisplayOpts`` class contains overlay type specific display
    settings. ``DisplayOpts`` instances are managed by :class:`Display`
    instances.


    The ``DisplayOpts`` class is not meant to be created directly - it is a
    base class for type specific implementations (e.g. the :class:`.VolumeOpts`
    class).


    The following attributes are available on all ``DisplayOpts`` instances:


    =============== ======================================================
    ``overlay``     The overlay object
    ``display``     The :class:`Display` instance that created this
                    ``DisplayOpts`` instance.
    ``overlayType`` The value of the :attr:`Display.overlayType` property
                    corresponding to the type of this ``DisplayOpts``
                    instance.
    ``overlayList`` The :class:`.OverlayList` instance, which contains all
                    overlays.
    ``displayCtx``  The :class:`.DisplayContext` instance which is
                    responsible for all ``Display`` and ``DisplayOpts``
                    instances.
    ``name``        A unique name for this ``DisplayOpts`` instance.
    =============== ======================================================


    .. warning:: :class:`DisplayOpts` sub-classes must not define any
                 properties with the same name as any of the :class:`Display`
                 properties.
    """


    bounds = props.Bounds(ndims=3)
    """Specifies a bounding box in the display coordinate system which is big
    enough to contain the overlay described by this ``DisplayOpts``
    instance.

    The values in this ``bounds`` property must be updated by ``DisplayOpts``
    subclasses whenever the spatial representation of their overlay changes.
    """


    def __init__(
            self,
            overlay,
            display,
            overlayList,
            displayCtx,
            **kwargs):
        """Create a ``DisplayOpts`` object.

        :arg overlay:     The overlay associated with this ``DisplayOpts``
                          instance.

        :arg display:     The :class:`Display` instance which owns this
                          ``DisplayOpts`` instance.

        :arg overlayList: The :class:`.OverlayList` which contains all
                          overlays.

        :arg displayCtx:  A :class:`.DisplayContext` instance describing
                          how the overlays are to be displayed.
        """

        self.__overlay     = overlay
        self.__display     = display
        self.__overlayType = display.overlayType
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        props.SyncableHasProperties.__init__(self, **kwargs)
        actions.ActionProvider     .__init__(self, overlayList, displayCtx)

        log.debug('{}.init [DC: {}] ({})'.format(
            type(self).__name__, id(displayCtx), id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.debug('{}.del ({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """This method must be called when this ``DisplayOpts`` instance
        is no longer needed.

        If a subclass overrides this method, the subclass implementation
        must call this method, **after** performing its own clean up.
        """
        actions.ActionProvider.destroy(self)

        self.detachAllFromParent()

        self.__overlay = None
        self.__display = None


    @classmethod
    def getVolumeProps(cls):
        """Intended to be overridden by sub-classes as needed.  Returns a list
        of property names which control the currently displayed
        volume/timepoint for 4D overlays. The default implementation returns
        an empty list.
        """
        return []


    @property
    def overlay(self):
        """Return the overlay associated with this ``DisplayOpts`` object.
        """
        return self.__overlay


    @property
    def display(self):
        """Return the :class:`.Display` that is managing this
        ``DisplayOpts`` object.
        """
        return self.__display


    @property
    def overlayType(self):
        """Return the type of this ``DisplayOpts`` object (the value of
        :attr:`Display.overlayType`).
        """
        return self.__overlayType


    @property
    def name(self):
        """Return the name of this ``DisplayOpts`` object. """
        return self.__name


    @property
    def referenceImage(self):
        """Return the reference image associated with this ``DisplayOpts``
        instance.

        Some non-volumetric overlay types (e.g. the :class:`.Mesh` -
        see :class:`.MeshOpts`) may have a *reference* :class:`.Nifti` instance
        associated with them, allowing the overlay to be localised in the
        coordinate space defined by the :class:`.Nifti`. The
        :class:`.DisplayOpts` sub-class which corresponds to
        such non-volumetric overlays should override this method to return
        that reference image.

        :class:`.DisplayOpts` sub-classes which are associated with volumetric
        overlays (i.e. :class:`.Nifti` instances) do not need to override
        this method - in this case, the overlay itself is considered to be
        its own reference image, and is returned by the base-class
        implementation of this method.

        .. note:: The reference :class:`.Nifti` instance returned by
                  sub-class implementations of this method must be in
                  the :class:`.OverlayList`.
        """

        if isinstance(self.overlay, fslimage.Nifti):
            return self.overlay
        return None


    def getLabels(self):
        """Generates some orientation labels for the overlay associated with
        this ``DisplayOpts`` instance.

        If the overlay is not a ``Nifti`` instance, or does not have a
        reference image set, the labels will represent an unknown orientation.

        Returns a tuple containing:

          - The ``(xlo, ylo, zlo, xhi, yhi, zhi)`` labels
          - The ``(xorient, yorient, zorient)`` orientations (see
            :meth:`.Image.getOrientation`)
        """

        refImage = self.referenceImage

        if refImage is None:
            return ('??????', [constants.ORIENT_UNKNOWN] * 3)

        opts = self.displayCtx.getOpts(refImage)

        xorient = None
        yorient = None
        zorient = None

        # If we are displaying in voxels/scaled voxels,
        # and this image is not the current display
        # image, then we do not show anatomical
        # orientation labels, as there's no guarantee
        # that all of the loaded overlays are in the
        # same orientation, and it can get confusing.
        if opts.transform in ('id', 'pixdim', 'pixdim-flip') and \
           self.displayCtx.displaySpace != refImage:
            xlo = 'Xmin'
            xhi = 'Xmax'
            ylo = 'Ymin'
            yhi = 'Ymax'
            zlo = 'Zmin'
            zhi = 'Zmax'

        # Otherwise we assume that all images
        # are aligned to each other, so we
        # estimate the current image's orientation
        # in the display coordinate system
        else:

            xform   = opts.getTransform('display', 'world')
            xorient = refImage.getOrientation(0, xform)
            yorient = refImage.getOrientation(1, xform)
            zorient = refImage.getOrientation(2, xform)

            xlo     = strings.anatomy['Nifti', 'lowshort',  xorient]
            ylo     = strings.anatomy['Nifti', 'lowshort',  yorient]
            zlo     = strings.anatomy['Nifti', 'lowshort',  zorient]
            xhi     = strings.anatomy['Nifti', 'highshort', xorient]
            yhi     = strings.anatomy['Nifti', 'highshort', yorient]
            zhi     = strings.anatomy['Nifti', 'highshort', zorient]

        return ((xlo, ylo, zlo, xhi, yhi, zhi),
                (xorient, yorient, zorient))
