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

import props

import fsl.utils.typedict  as td
import fsl.data.image      as fslimage
import fsl.fsleyes.actions as actions


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
    method, from the :attr:`OVERLAY_TYPES` dictionary. A :class:`DisplayOpts`
    sub-class exists for every possible value that this property may take.
    """
    
    enabled = props.Boolean(default=True)
    """Should this overlay be displayed at all? """

    
    alpha = props.Percentage(default=100.0)
    """Opacity - 100% is fully opaque, and 0% is fully transparent."""

    
    brightness = props.Percentage()
    """Brightness - 50% is normal brightness."""

    
    contrast   = props.Percentage()
    """Contrast - 50% is normal contrast."""


    softwareMode = props.Boolean(default=False)
    """If possible, optimise for a low-performance rendering environment
    (e.g. a software-based OpenGL renderer).
    """

    
    def __init__(self,
                 overlay,
                 overlayList,
                 displayCtx,
                 parent=None,
                 overlayType=None):
        """Create a :class:`Display` for the specified overlay.

        :arg overlay:     The overlay object.

        :arg overlayList: The :class:`.OverlayList` instance which contains
                          all overlays.

        :arg displayCtx:  A :class:`.DisplayContext` instance describing how
                          the overlays are to be displayed.

        :arg parent:      A parent ``Display`` instance - see
                          :mod:`props.syncable`.

        :arg overlayType: Initial overlay type - see the :attr:`overlayType`
                          property.
        """
        
        self.__overlay     = overlay
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.name          = overlay.name

        # Populate the possible choices
        # for the overlayType property
        overlayTypeProp = self.getProp('overlayType')
        possibleTypes   = list(OVERLAY_TYPES[overlay])

        # Special cases:
        #
        # If the overlay is an image which
        # does not have a fourth dimension
        # of length three, it can't be
        # a vector
        if isinstance(overlay, fslimage.Image) and \
           (len(overlay.shape) != 4 or overlay.shape[-1] != 3):
            possibleTypes.remove('rgbvector')
            possibleTypes.remove('linevector')
            
        for pt in possibleTypes:
            log.debug('Enabling overlay type {} for {}'.format(pt, overlay))
            overlayTypeProp.addChoice(pt, instance=self)

        if overlayType is not None:
            self.overlayType = overlayType

        # Call the super constructor after our own
        # initialisation, in case the provided parent
        # has different property values to our own,
        # and our values need to be updated
        props.SyncableHasProperties.__init__(
            self, parent=parent,

            # These properties cannot be unbound, as
            # they affect the OpenGL representation 
            nounbind=['softwareMode', 'overlayType'],

            # Initial sync state between this
            # Display and the parent Display
            # (if this Display has a parent)
            state=displayCtx.syncOverlayDisplay)

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
        self.__oldOptValues = td.TypeDict()

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

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))

        
    def __del__(self):
        """Prints a log message."""
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

    
    def getOverlay(self):
        """Returns the overlay associated with this ``Display`` instance."""
        return self.__overlay


    def destroy(self):
        """This method must be called when this ``Display`` instance
        is no longer needed.

        When a ``Display`` instance is destroyed, the corresponding
        :class:`DisplayOpts` instance is also destroyed.
        """
        
        if self.__displayOpts is not None:
            self.__displayOpts.destroy()

        self.removeListener('overlayType', 'Display_{}'.format(id(self)))

        self.detachFromParent()
        
        self.__displayOpts = None
        self.__overlayList = None
        self.__displayCtx  = None
        self.__overlay     = None
        
        
    def getDisplayOpts(self):
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

        The :data:`DISPLAY_OPTS_MAP` dictionary defines the mapping between
        :attr:`overlayType` values, and ``DisplayOpts`` sub-class types.
        """

        if self.getParent() is None:
            oParent = None
        else:
            oParent = self.getParent().getDisplayOpts()

        optType = DISPLAY_OPTS_MAP[self.overlayType]
        
        log.debug('Creating {} instance for overlay {} ({})'.format(
            optType.__name__, self.__overlay, self.overlayType))
        
        return optType(self.__overlay,
                       self,
                       self.__overlayList,
                       self.__displayCtx,
                       parent=oParent,
                       state=self.__displayCtx.syncOverlayDisplay)


    def __findOptBaseType(self, optType):
        """Finds the top level base class for the given :class:`DisplayOpts`
        subclass.

        This method is used by the :meth:`__saveOldDisplayOpts` method, and
        is an annoying necessity caused by the way that the :class:`.TypeDict`
        class works. A ``TypeDict`` does not allow types to be used as keys -
        they must be strings containing the type names.

        Furthermore, in order for the property values of a common
        ``DisplayOpts`` base type to be shared across sub types (e.g. copying
        the :attr:`.ImageOpts.transform` property between :class:`.VolumeOpts`
        and :class:`.LabelOpts` instances), we need to store the name of the
        common base type in the dictionary.

        So this method just recursively finds and returns the highest base
        type of the given ``optType`` which is a sub-type of ``DisplayOpts``.
        """

        bases = optType.__bases__

        if DisplayOpts in bases:
            return optType

        for base in bases:
            
            base = self.__findOptBaseType(base)
            if base is not None:
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
            base = self.__findOptBaseType(type(opts))
            base = base.__name__
            self.__oldOptValues[base, propName] = getattr(opts, propName)

    
    def __restoreOldDisplayOpts(self):
        """Restores any cached values for all of the properties on the
        current :class:`DisplayOpts` instance.
        """
        opts = self.__displayOpts

        if opts is None:
            return

        for propName in opts.getAllProperties()[0]:
            
            try:
                value = self.__oldOptValues[opts, propName]
                setattr(opts, propName, value)
                
            except KeyError:
                pass
                
    
    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`overlayType` property changes. Makes sure
        that the :class:`DisplayOpts` instance is of the correct type.
        """
        self.__saveOldDisplayOpts()
        self.getDisplayOpts()
        self.__restoreOldDisplayOpts()


class DisplayOpts(actions.ActionProvider):
    """The ``DisplayOpts`` class contains overlay type specific display
    settings. ``DisplayOpts`` instances are managed by :class:`Display`
    instances.

    
    The ``DisplayOpts`` class is not meant to be created directly - it is a
    base class for type specific implementations (e.g. the :class:`.ImageOpts`
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
    ``name``        A unique name for this ``DIsplayOpts`` instance.
    =============== ======================================================
    """


    bounds = props.Bounds(ndims=3)
    """Specifies a bounding box in the display coordinate system which is big
    enough to contain the overlay described by this ``DisplayOpts``
    instance. The values in this ``bounds`` property must be updated by
    ``DisplayOpts`` subclasses.

    Whenever the spatial representation of this overlay changes, but the
    bounds do not change, subclass implementations should force notification
    on this property (via the :meth:`.HasProperties.notify` method).
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
        
        :arg kwargs:      Passed through to the
                          :class:`.ActionProvider` constructor.
        """

        actions.ActionProvider.__init__(
            self,
            overlayList,
            displayCtx,
            **kwargs)
        
        self.overlay     = overlay
        self.display     = display
        self.overlayList = overlayList
        self.displayCtx  = displayCtx
        self.overlayType = display.overlayType
        self.name        = '{}_{}'.format(type(self).__name__, id(self))

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))

        
    def __del__(self):
        """Prints a log message."""
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

        
    def destroy(self):
        """This method must be called when this ``DisplayOpts`` instance
        is no longer needed.

        If a subclass overrides this method, the subclass implementation
        must call this method, **after** performing its own clean up.
        """
        actions.ActionProvider.destroy(self)

        self.overlay     = None
        self.display     = None
        self.overlayList = None
        self.displayCtx  = None


    def getReferenceImage(self):
        """Return the reference image associated with this ``DisplayOpts``
        instance.

        Some non-volumetric overlay types (e.g. the :class:`.Model` - see
        :class:`.ModelOpts`) may have a *reference* :class:`.Image` instance
        associated with them, allowing the overlay to be localised in the
        coordinate space defined by the :class:`.Image`. The
        :class:`.DisplayOpts` sub-class which corresponds to
        such non-volumetric overlays should override this method to return
        that reference image.

        :class:`.DisplayOpts` sub-classes which are associated with volumetric
        overlays (i.e. :class:`.Image` instances) do not need to override
        this method - in this case, the overlay itself is considered to be
        its own reference image, and is returned by the base-class
        implementation of this this method.
        """

        if isinstance(self.overlay, fslimage.Image):
            return self.overlay
        return None

    
    def transformDisplayLocation(self, coords):
        """This method may be called after the overlay :attr:`bounds` have
        changed.

        If the bounds were changed as a result of a change to the spatial
        representation of the overlay (e.g. the :attr:`.ImageOpts.transform`
        property for :class:`.Image` overlays), this method should return
        a copy of the given coordinates which has been transformed into the
        new space.

        If the bounds were changed for some other reason, this method can
        just return the ``coords`` unchanged.
        """
        return coords


import volumeopts
import vectoropts
import maskopts
import labelopts
import modelopts


OVERLAY_TYPES = td.TypeDict({

    'Image' : ['volume', 'mask', 'rgbvector', 'linevector', 'label'],
    'Model' : ['model']
})
"""This dictionary provides a mapping between all overlay classes,
and the possible values that the :attr:`Display.overlayType` property
may take for each of them. 

For each overlay class, the first entry in the corresponding overlay type
list is used as the default overlay type.
"""


DISPLAY_OPTS_MAP = {
    'volume'     : volumeopts.VolumeOpts,
    'rgbvector'  : vectoropts.RGBVectorOpts,
    'linevector' : vectoropts.LineVectorOpts,
    'mask'       : maskopts.  MaskOpts,
    'model'      : modelopts. ModelOpts,
    'label'      : labelopts. LabelOpts,
}
"""This dictionary provides a mapping between each overlay type, and
the :class:`DisplayOpts` subclass which contains overlay type-specific
display options.
"""
