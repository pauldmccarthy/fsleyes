#!/usr/bin/env python
#
# colourmapopts.py - The ColourMapOpts class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourMapOpts` class, a mixin for use with
:class:`.DisplayOpts` sub-classes.
"""


import logging

import fsleyes_props      as props
import fsleyes.actions    as actions
import fsleyes.colourmaps as fslcm


log = logging.getLogger(__name__)


class ColourMapOpts(object):
    """The ``ColourMapOpts`` class is a mixin for use with
    :class:`.DisplayOpts` sub-classes. It provides properties and logic
    for displaying overlays which are coloured according to some data values.
    See the :class:`.MeshOpts` and :class:`.VolumeOpts` classes for examples
    of classes which inherit from this class.


    To use the ``ColourMapOpts`` class, you must:

      1. Define your class to inherit from both :class:`.DisplayOpts` and
         ``ColourMapOpts``::

             class MyOpts(DisplayOpts, ColourMapOpts):
                 ...

      2. Call the ``ColourMapOpts.__init__`` method *after*
         :meth:`.DisplayOpts.__init__`::

             def __init__(self, *args, **kwargs):
                 DisplayOpts.__init__(self, *args, **kwargs)
                 ColourMapOpts.__init__(self)

      3. Implement the :meth:`getDataRange` and (if necessary)
         :meth:`getClippingRange` and :meth:`getModulateRange` methods.

      4. Call :meth:`updateDataRange` whenever the data driving the colouring
         changes.


    The ``ColourMapOpts`` class links the :attr:`.Display.brightness` and
    :attr:`.Display.contrast` properties to its own :attr:`displayRange`
    property, so changes in either of the former will result in a change to
    the latter, and vice versa. This relationship is defined by the
    :func:`~.colourmaps.displayRangeToBricon` and
    :func:`~.colourmaps.briconToDisplayRange` functions, in the
    :mod:`.colourmaps` module.


    ``ColourMapOpts`` instances provide the following methods:

    .. autosummary::
       :nosignatures:

       updateDataRange
       getDataRange
       getClippingRange
       getModulateRange
    """


    displayRange = props.Bounds(ndims=1, clamped=False)
    """Values which map to the minimum and maximum colour map colours.

    .. note:: The values that this property can take are unbound because of
              the interaction between it and the :attr:`.Display.brightness`
              and :attr:`.Display.contrast` properties.  The
              :attr:`displayRange` and :attr:`clippingRange` properties are
              not clamped (they can take values outside of their
              minimum/maximum values) because the data range for large NIFTI
              images may not be known, and may change as more data is read
              from disk.
    """


    clippingRange = props.Bounds(ndims=1, clamped=False)
    """Values outside of this range are not shown.  Clipping works as follows:

     - Values less than or equal to the minimum clipping value are
       clipped.

     - Values greater than or equal to the maximum clipping value are
       clipped.

    Because of this, a small amount of padding is added to the low and high
    clipping range limits, to make it possible for all values to be
    displayed.
    """


    invertClipping = props.Boolean(default=False)
    """If ``True``, the behaviour of :attr:`clippingRange` is inverted, i.e.
    values inside the clipping range are clipped, instead of those outside
    the clipping range.
    """


    cmap = props.ColourMap()
    """The colour map, a :class:`matplotlib.colors.Colourmap` instance."""


    gamma = props.Real(minval=-1, maxval=1, clamped=True, default=0)
    """Gamma correction factor - exponentially weights the :attr:`cmap`
    and :attr:`negCmap` towards the low or high ends.

    This property takes values between -1 and +1. The exponential weight
    that should actually be used to apply gamma correction should be derived
    as follows:

      - -1 corresponds to a gamma of 0.01
      -  0 corresponds to a gamma of 1
      - +1 corresponds to a gamma of 10

    The :meth:`realGamma` method will apply this scaling and return the
    exponent to be used.
    """


    cmapResolution = props.Int(minval=2, maxval=1024, default=256)
    """Resolution for the colour map, i.e. the number of colours to use. """


    interpolateCmaps = props.Boolean(default=False)
    """If ``True``, the colour maps are applied using linear interpolation.
    Otherwise they are applied using nearest neighbour interpolation.
    """


    negativeCmap = props.ColourMap()
    """A second colour map, used if :attr:`useNegativeCmap` is ``True``.
    When active, the :attr:`cmap` is used to colour positive values, and
    the :attr:`negativeCmap` is used to colour negative values.
    """


    useNegativeCmap = props.Boolean(default=False)
    """When ``True``, the :attr:`cmap` is used to colour positive values,
    and the :attr:`negativeCmap` is used to colour negative values.
    When this property is enabled, the minimum value for both the
    :attr:`displayRange` and :attr:`clippingRange` is set to zero. Both
    ranges are applied to positive values, and negated/inverted for negative
    values.

    .. note:: When this property is set to ``True``, the
              :attr:`.Display.brightness` and :attr:`.Display.contrast`
              properties are disabled, as managing the interaction between
              them would be far too complicated.
    """


    invert = props.Boolean(default=False)
    """Use an inverted version of the current colour map (see the :attr:`cmap`
    property).
    """


    linkLowRanges = props.Boolean(default=True)
    """If ``True``, the low bounds on both the :attr:`displayRange` and
    :attr:`clippingRange` ranges will be linked together.
    """


    linkHighRanges = props.Boolean(default=False)
    """If ``True``, the high bounds on both the :attr:`displayRange` and
    :attr:`clippingRange` ranges will be linked together.
    """


    modulateAlpha = props.Boolean(default=False)
    """If ``True``, the :attr:`.Display.alpha` is modulated by the data.
    Regions with a value near to the low :attr:`modulateRange` will have an
    alpha near 0, and regions with a value near to the high
    :attr:`modulateRange` will have an alpha near 1.
    """


    modulateRange = props.Bounds(ndims=1)
    """Range used to determine how much to modulate :attr:`.Display.alpha`
    by, when :attr:`modulateAlpha` is active.
    """


    @staticmethod
    def realGamma(gamma):
        """Return the value of ``gamma`` property, scaled appropriately.
        for use as an exponent.
        """

        # a gamma in the range [-1, 0]
        # gets scaled to [0.01, 1]
        if gamma < 0:
            return (gamma + 1.01) * 0.99

        # a gamma in the range [0, 1]
        # gets scaled to [1, 10]
        else:
            return 1 + 9 * gamma


    def __init__(self):
        """Create a ``ColourMapOpts`` instance. This must be called
        *after* the :meth:`.DisplayOpts.__init__` method.
        """

        # The displayRange property of every child ColourMapOpts
        # instance is linked to the corresponding
        # Display.brightness/contrast properties, so changes
        # in one are reflected in the other. This interaction
        # complicates the relationship between parent and child
        # ColourMapOpts instances, so we only implement it on
        # children.
        #
        # NOTE: This means that if we use a parent-less
        #       DisplayContext for display, this bricon-display
        #       range relationship will break.
        #
        self.__registered = self.getParent() is not None

        if self.__registered:

            name    = self.getColourMapOptsListenerName()
            display = self.display

            display.addListener('brightness',
                                name,
                                self.__briconChanged,
                                immediate=True)
            display.addListener('contrast',
                                name,
                                self.__briconChanged,
                                immediate=True)
            self   .addListener('displayRange',
                                name,
                                self.__displayRangeChanged,
                                immediate=True)
            self   .addListener('useNegativeCmap',
                                name,
                                self.__useNegativeCmapChanged,
                                immediate=True)
            self   .addListener('linkLowRanges',
                                name,
                                self.__linkLowRangesChanged,
                                immediate=True)
            self   .addListener('linkHighRanges',
                                name,
                                self.__linkHighRangesChanged,
                                immediate=True)
            self   .addListener('modulateAlpha',
                                name,
                                self.__modulateAlphaChanged,
                                immediate=True)

            # Because displayRange and bri/con are intrinsically
            # linked, it makes no sense to let the user sync/unsync
            # them independently. So here we are binding the boolean
            # sync properties which control whether the dRange/bricon
            # properties are synced with their parent. So when one
            # property is synced/unsynced, the other ones are too.
            self.bindProps(self   .getSyncPropertyName('displayRange'),
                           display,
                           display.getSyncPropertyName('brightness'))
            self.bindProps(self   .getSyncPropertyName('displayRange'),
                           display,
                           display.getSyncPropertyName('contrast'))

            # If useNegativeCmap, linkLowRanges or linkHighRanges
            # have been set to True (this will happen if they
            # are true on the parent VolumeOpts instance), make
            # sure the property / listener states are up to date.
            if self.linkLowRanges:   self.__linkLowRangesChanged()
            if self.linkHighRanges:  self.__linkHighRangesChanged()
            if self.useNegativeCmap:
                self.__useNegativeCmapChanged(updateDataRange=False)

        # If this is the parent ColourMapOpts
        # instance, its properties need to be
        # initialised. Child instance properties
        # should inherit the current parent
        # values, unless they are not synced
        # to the parent.
        if (not self.__registered) or \
           (not self.isSyncedToParent('displayRange')):
            self.updateDataRange(False, False, False)


    def getColourMapOptsListenerName(self):
        """Returns the name used by this ``ColourMapOpts`` instance for
        registering internal property listeners.

        Sibling ``ColourMapOpts``
        instances need to toggle each other's property listeners (see the
        :meth:`__toggleListeners` method), so they use this method to
        retrieve each other's listener names.
        """
        return 'ColourMapOpts_{}'.format(id(self))


    def destroy(self):
        """Must be called when this ``ColourMapOpts`` is no longer needed,
        and before :meth:`.DisplayOpts.destroy` is called. Removes property
        listeners.
        """

        if not self.__registered:
            return

        display = self.display
        name    = self.getColourMapOptsListenerName()

        display.removeListener('brightness',      name)
        display.removeListener('contrast',        name)
        self   .removeListener('displayRange',    name)
        self   .removeListener('useNegativeCmap', name)
        self   .removeListener('linkLowRanges',   name)
        self   .removeListener('linkHighRanges',  name)
        self   .removeListener('modulateAlpha',   name)

        self.unbindProps(self   .getSyncPropertyName('displayRange'),
                         display,
                         display.getSyncPropertyName('brightness'))
        self.unbindProps(self   .getSyncPropertyName('displayRange'),
                         display,
                         display.getSyncPropertyName('contrast'))

        self.__linkRangesChanged(False, 0)
        self.__linkRangesChanged(False, 1)


    def getDataRange(self):
        """Must be overridden by sub-classes. Must return the range of the
        data used for colouring as a ``(min, max)`` tuple.  Note that, even
        if there is no effective data range, you should return two different
        values for ``min`` and ``max`` (e.g. ``(0, 1)``), because otherwise
        the relationship between the :attr:`displayRange` and the
        :attr:`.Display.brightness` and :attr:`.Display.contrast` properties
        will be corrupted.
        """

        raise NotImplementedError('ColourMapOpts.getDataRange must be '
                                  'implemented by sub-classes.')


    def getClippingRange(self):
        """Can be overridden by sub-classes if necessary. If the clipping
        range is always the same as the data range, this method does not
        need to be overridden.

        Otherwise, if the clipping range differs from the data range
        (see e.g. the :attr:`.VolumeOpts.clipImage` property), this method
        must return the clipping range as a ``(min, max)`` tuple.

        When a sub-class implementation wishes to use the default clipping
        range/behaviour, it should return the value returned by this
        base-class implementation.
        """
        return None


    def getModulateRange(self):
        """Can be overridden by sub-classes if necessary. If the modulate
        range is always the same as the data range, this method does not
        need to be overridden.

        Otherwise, if the modulate ange differs from the data range (see
        e.g. the :attr:`.VolumeOpts.modulateImage` property), this method must
        return the modulate range as a ``(min, max)`` tuple.

        When a sub-class implementation wishes to use the default modulate
        range/behaviour, it should return the value returned by this
        base-class implementation.
        """
        return None


    @actions.action
    def resetDisplayRange(self):
        """Resets the :attr:`displayRange`, :attr:`clippingRange`, and
         :attr:`modulateRange` to their initial values.
        """
        self.updateDataRange(True, True, True)


    def updateDataRange(self, resetDR=True, resetCR=True, resetMR=True):
        """Must be called by sub-classes whenever the ranges of the underlying
        data or clipping/modulate values change.  Configures the minimum/
        maximum bounds of the :attr:`displayRange`, :attr:`clippingRange`, and
        :attr:`modulateRange` properties.

        :arg resetDR: If ``True`` (the default), the :attr:`displayRange`
                      property will be reset to the data range returned
                      by :meth:`getDataRange`. Otherwise the existing
                      value will be preserved.

        :arg resetCR: If ``True`` (the default), the :attr:`clippingRange`
                      property will be reset to the clipping range returned
                      by :meth:`getClippingRange`. Otherwise the existing
                      value will be preserved.

        :arg resetMR: If ``True`` (the default), the :attr:`modulateRange`
                      property will be reset to the modulate range returned
                      by :meth:`getModulateRange`. Otherwise the existing
                      value will be preserved.

        Note that both of these flags will be ignored if the existing low/high
        :attr:`displayRange`/:attr:`clippingRange`/:attr:`modulateRange`
        values and limits are equal to each other.
        """

        dataMin, dataMax = self.getDataRange()
        clipRange        = self.getClippingRange()
        modRange         = self.getModulateRange()

        absolute = self.useNegativeCmap
        drmin    = dataMin
        drmax    = dataMax

        if absolute:
            drmin = min((0,            abs(dataMin)))
            drmax = max((abs(dataMin), abs(dataMax)))

        if clipRange is not None: crmin, crmax = clipRange
        else:                     crmin, crmax = drmin, drmax

        if modRange  is not None: mrmin, mrmax = modRange
        else:                     mrmin, mrmax = drmin, drmax

        # Clipping works on >= and <=, so we add
        # a small offset to the display range limits
        # (which are equal to the clipping limiits)
        # so the user can configure the scene such
        # that no values are clipped.
        droff  = abs(drmax - drmin) / 100.0
        croff  = abs(crmax - crmin) / 100.0
        crmin -= croff
        crmax += croff
        drmin -= droff
        drmax += droff

        # Execute on the PV call queue,
        # so that property updates occur
        # in the correct order.
        def doUpdate():

            # If display/clipping/mod limit range
            # is 0, we assume that they haven't
            # yet been set
            drUnset = (self.displayRange .xmin == self.displayRange .xmax and
                       self.displayRange .xlo  == self.displayRange .xhi)
            crUnset = (self.clippingRange.xmin == self.clippingRange.xmax and
                       self.clippingRange.xlo  == self.clippingRange.xhi)
            mrUnset = (self.modulateRange.xmin == self.modulateRange.xmax and
                       self.modulateRange.xlo  == self.modulateRange.xhi)
            crGrow  =  self.clippingRange.xhi  == self.clippingRange.xmax
            drUnset =  resetDR or drUnset
            crUnset =  resetCR or crUnset
            mrUnset =  resetMR or mrUnset

            log.debug('[%s] Updating range limits [dr: %s - %s, cr: '
                      '%s - %s, mr: %s - %d]',
                      id(self), drmin, drmax, crmin, crmax, mrmin, mrmax)

            self.displayRange .xlim = drmin, drmax
            self.clippingRange.xlim = crmin, crmax
            self.modulateRange.xlim = mrmin, mrmax

            # If the ranges have not yet been set,
            # initialise them to the min/max.
            # Also, if the high clipping range
            # was previously equal to the max
            # clipping range, keep that relationship,
            # otherwise high values will be clipped.
            if drUnset: self.displayRange .x   = drmin + droff, drmax
            if crUnset: self.clippingRange.x   = crmin + croff, crmax
            if mrUnset: self.modulateRange.x   = mrmin,         mrmax
            if crGrow:  self.clippingRange.xhi = crmax

            # If using absolute range values, the
            # low range values should be set to 0
            if absolute and self.displayRange .xlo < 0:
                self.displayRange.xlo  = 0
            if absolute and self.clippingRange.xlo < 0:
                self.clippingRange.xlo = 0
            if absolute and self.modulateRange.xlo < 0:
                self.modulateRange.xlo = 0

        props.safeCall(doUpdate)


    def __toggleListeners(self, enable=True):
        """This method enables/disables the property listeners which
        are registered on the :attr:`displayRange` and
        :attr:`.Display.brightness`/:attr:`.Display.contrast`/properties.

        Because these properties are linked via the
        :meth:`__displayRangeChanged` and :meth:`__briconChanged` methods,
        we need to be careful about avoiding recursive callbacks.

        Furthermore, because the properties of both :class:`ColourMapOpts` and
        :class:`.Display` instances are possibly synchronised to a parent
        instance (which in turn is synchronised to other children), we need to
        make sure that the property listeners on these other sibling instances
        are not called when our own property values change. So this method
        disables/enables the property listeners on all sibling
        ``ColourMapOpts`` and ``Display`` instances.
        """

        parent = self.getParent()

        # this is the parent instance
        if parent is None:
            return

        # The parent.getChildren() method will
        # contain this ColourMapOpts instance,
        # so the below loop toggles listeners
        # for this instance and all of the other
        # children of the parent
        peers  = parent.getChildren()

        for peer in peers:

            name = peer.getColourMapOptsListenerName()
            bri  = peer.display.hasListener('brightness',   name)
            con  = peer.display.hasListener('contrast',     name)
            dr   = peer        .hasListener('displayRange', name)

            if enable:
                if bri: peer.display.enableListener('brightness',   name)
                if con: peer.display.enableListener('contrast',     name)
                if dr:  peer        .enableListener('displayRange', name)
            else:
                if bri: peer.display.disableListener('brightness',   name)
                if con: peer.display.disableListener('contrast',     name)
                if dr:  peer        .disableListener('displayRange', name)


    def __briconChanged(self, *a):
        """Called when the ``brightness``/``contrast`` properties of the
        :class:`.Display` instance change.

        Updates the :attr:`displayRange` property accordingly.

        See :func:`.colourmaps.briconToDisplayRange`.
        """

        dataRange = self.getDataRange()

        dlo, dhi = fslcm.briconToDisplayRange(
            dataRange,
            self.display.brightness / 100.0,
            self.display.contrast   / 100.0)

        self.__toggleListeners(False)
        self.displayRange.x = [dlo, dhi]
        self.__toggleListeners(True)


    def __displayRangeChanged(self, *a):
        """Called when the `attr:`displayRange` property changes.

        Updates the :attr:`.Display.brightness` and :attr:`.Display.contrast`
        properties accordingly.

        See :func:`.colourmaps.displayRangeToBricon`.
        """

        if self.useNegativeCmap:
            return

        dataRange = self.getDataRange()

        brightness, contrast = fslcm.displayRangeToBricon(
            dataRange, self.displayRange.x)

        self.__toggleListeners(False)

        # update bricon
        self.display.brightness = brightness * 100
        self.display.contrast   = contrast   * 100

        self.__toggleListeners(True)


    def __useNegativeCmapChanged(self, *a, **kwa):
        """Called when the :attr:`useNegativeCmap` property changes.
        Enables/disables the :attr:`.Display.brightness` and
        :attr:`.Display.contrast` properties, and calls
        :meth:`updateDataRange`.

        :arg updateDatRange: Must be passed as a keyword argument.
                             If ``True`` (the default), calls
                             :meth:`updateDataRange`.
        """

        if self.useNegativeCmap:
            self.display.disableProperty('brightness')
            self.display.disableProperty('contrast')
        else:
            self.display.enableProperty('brightness')
            self.display.enableProperty('contrast')

        if kwa.pop('updateDataRange', True):
            self.updateDataRange(False, False, False)


    def __linkLowRangesChanged(self, *a):
        """Called when the :attr:`linkLowRanges` property changes. Calls the
        :meth:`__linkRangesChanged` method.
        """
        self.__linkRangesChanged(self.linkLowRanges, 0)


    def __linkHighRangesChanged(self, *a):
        """Called when the :attr:`linkHighRanges` property changes. Calls the
        :meth:`__linkRangesChanged` method.
        """
        self.__linkRangesChanged(self.linkHighRanges, 1)


    def __linkRangesChanged(self, val, idx):
        """Called when either the :attr:`linkLowRanges` or
        :attr:`linkHighRanges` properties change. Binds/unbinds the specified
        range properties together.

        :arg val: Boolean indicating whether the range values should be
                  linked or unlinked.

        :arg idx: Range value index - 0 corresponds to the low range value,
                  and 1 to the high range value.
        """

        dRangePV = self.displayRange .getPropertyValueList()[idx]
        cRangePV = self.clippingRange.getPropertyValueList()[idx]

        if props.propValsAreBound(dRangePV, cRangePV) == val:
            return

        props.bindPropVals(dRangePV,
                           cRangePV,
                           bindval=True,
                           bindatt=False,
                           unbind=not val)

        if val:
            cRangePV.set(dRangePV.get())


    def __modulateAlphaChanged(self, *a):
        """Called when the :attr:`modulateAlpha` property changes.

        When ``modulateAlpha`` is active, :attr:`.Display.alpha` is disabled,
        and vice-versa.
        """

        if self.modulateAlpha:
            self.display.disableProperty('alpha')
        else:
            self.display.enableProperty('alpha')
