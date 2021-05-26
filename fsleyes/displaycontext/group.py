#!/usr/bin/env python
#
# group.py - Overlay groups
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OverlayGroup` class, which allows
the display properties of one or more overlays to be linked.
"""


import sys
import copy
import logging


import fsleyes_props                  as props
import fsleyes_widgets.utils.typedict as td


log = logging.getLogger(__name__)


class OverlayGroup(props.HasProperties):
    """An ``OverlayGroup`` is a group of overlays for which the corresponding
    :class:`.Display` and :class:`.DisplayOpts` properties are synchronised.


    The point of the ``OverlayGroup`` is to allow the user to define groups of
    overlays, so he/she can change display properties on the entire group,
    instead of having to change display properties on each overlay one by one.


    Overlays can be added to an ``OverlayGroup`` with the :meth:`addOverlay`,
    and removed with the :meth:`removeOverlay`.


    When an ``OverlayGroup`` is created, it dynamically adds all of the
    properties which could possibly be linked between overlays to itself,
    using the :meth:`props.HasProperties.addProperty` method. When the first
    overlay is added to the group, these group properties are set to the
    display properties of this overlay. Then, the display properties of
    overlays which are subsequently added to the group will be set to the
    group display properties.


    .. note:: Currently, only a subset of display properties are linked
              between the overlays in a group. The properties which are linked
              are hard-coded in the :attr:`_groupBindings` dictionary.

              A possible future *FSLeyes* enhancement will be to allow the
              user to specify which display properties within an
              ``OverlayGroup`` should be linked.
    """


    overlays = props.List()
    """The list of overlays in this ``OverlayGroup``.

    .. warning:: Do not add/remove overlays directly to this list - use the
                :meth:`addOverlay` and :meth:`removeOverlay` methods instead.
    """


    _groupBindings = td.TypeDict({
        'Display'        : [],
        'NiftiOpts'      : ['volume',
                            'volumeDim'],
        'VolumeOpts'     : ['interpolation'],
        'Volume3DOpts'   : ['numSteps',
                            'numInnerSteps',
                            'resolution',
                            'numClipPlanes',
                            'clipMode',
                            'clipPosition',
                            'clipAzimuth',
                            'clipInclination'],
        'LabelOpts'      : [],
        'MeshOpts'       : ['refImage',
                            'coordSpace'],
        'VectorOpts'     : ['suppressX',
                            'suppressY',
                            'suppressZ',
                            'suppressMode'],
        'LineVectorOpts' : [],
        'RGBVectorOpts'  : ['interpolation'],
        'TensorOpts'     : ['lighting',
                            'tensorResolution'],
    })
    """This dictionary defines the properties which are bound across
    :class:`.Display` instances :class:`.DisplayOpts` sub-class instances, for
    overlays which are in the same group.
    """


    def __init__(self, displayCtx, overlayList):
        """Create an ``OverlayGroup``.

        :arg displayCtx:  The :class:`.DisplayContext`.

        :arg overlayList: The :class:`.OverlayList`.
        """

        # Import all of the Display/DisplayOpts
        # classes into the local namespace.
        from fsleyes.displaycontext import (  # noqa
            Display,
            NiftiOpts,
            VolumeOpts,
            Volume3DOpts,
            MaskOpts,
            VectorOpts,
            RGBVectorOpts,
            LineVectorOpts,
            MeshOpts,
            LabelOpts,
            TensorOpts)

        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        # This dict is used by the __bindDisplayOpts
        # method to keep track of which group properties
        # have already been given a value
        self.__hasBeenSet  = {}

        # Save a ref to each type so we
        # can look up classes by name.
        self.__typeMappings = {}
        for clsName in OverlayGroup._groupBindings.keys():
            self.__typeMappings[clsName] = locals()[clsName]

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)

        # Add all of the properties listed
        # in the _groupBindings dict as
        # properties of this OverlayGroup
        # instance.
        for clsName, propNames in OverlayGroup._groupBindings.items():

            cls = self.__typeMappings[clsName]

            for propName in propNames:
                prop = copy.copy(getattr(cls, propName))
                self.addProperty('{}_{}'.format(clsName, propName), prop)
                self.__hasBeenSet[clsName, propName] = False

        # Special case - make sure that the NiftiOpts
        # volume property is not constrained
        self.setAttribute('NiftiOpts_volume', 'maxval', sys.maxsize)


    def __copy__(self):
        """Create a copy of this ``OverlayGroup``.

        A custom copy operator is needed due to the way that
        the :class:`.props.HasProperties` class works.
        """
        return OverlayGroup(self, self.__displayCtx, self.__overlayList)


    def __str__(self):
        """Returns a string representation of this ``OverlayGroup``."""
        return str([str(o) for o in self.overlays])


    def __repr__(self):
        """Returns a string representation of this ``OverlayGroup``."""
        return '[{}]'.format(', '.join([str(o) for o in self.overlays]))


    def __contains__(self, ovl):
        """Returns ``True`` if ``ovl`` is in this ``OverlayGroup``,
        :attr:`False` otherwise.
        """
        return ovl in self.overlays


    def __len__(self):
        """Returns the number of overlays in this ``OverlayGroup``. """
        return len(self.overlays)


    def destroy(self):
        """Must be called when this ``OverlayGroup`` is no longer needed.
        Removes all overlays from the group, and removes property listeners.
        """
        for overlay in list(self.overlays):
            self.removeOverlay(overlay)

        self.__overlayList.removeListener('overlays', self.__name)

        self.__overlayList = None
        self.__displayCtx  = None


    def addOverlay(self, overlay):
        """Add an overlay to this ``OverlayGroup``.

        If this is the first overlay to be added, the properties of this
        ``OverlayGroup`` are set to the overlay display properties. Otherwise,
        the overlay display properties are set to those of this
        ``OverlayGroup``.
        """

        if overlay in self.overlays:
            return

        self.overlays.append(overlay)

        display = self.__displayCtx.getDisplay(overlay)
        opts    = display.opts

        log.debug('Adding overlay {} to group {}'.format(
            overlay.name, self.__name))

        self.__bindDisplayOpts(display)
        self.__bindDisplayOpts(opts)

        display.addListener('overlayType',
                            self.__name,
                            self.__overlayTypeChanged)


    def removeOverlay(self, overlay):
        """Remove the given overlay from this ``OverlayGroup``. """

        if overlay not in self.overlays:
            return

        from . import InvalidOverlayError

        self.overlays.remove(overlay)

        try:
            display = self.__displayCtx.getDisplay(overlay)
        except InvalidOverlayError:
            return

        opts = display.opts

        log.debug('Removing overlay {} from group {}'.format(
            overlay.name, self.__name))

        self.__bindDisplayOpts(display, unbind=True)
        self.__bindDisplayOpts(opts,    unbind=True)

        display.removeListener('overlayType', self.__name)

        # If this was the last overlay of its type,
        # make sure to clear the hasBeenSet flag
        # for all relevent properties; otherwise
        # the properties of the next overlay of
        # this type to be added will be clobbered
        # by the old group values.
        allopts   = [self.__displayCtx.getOpts(o) for o in self.overlays]
        bindProps = OverlayGroup._groupBindings.get(opts,
                                                    allhits=True,
                                                    bykey=True)
        for clsName, propNames in bindProps.items():

            cls     = self.__typeMappings[clsName]
            noftype = len([o for o in allopts if issubclass(type(o), cls)])

            if noftype == 0:
                for propName in propNames:
                    self.__hasBeenSet[clsName, propName] = False


    def __bindDisplayOpts(self, target, unbind=False):
        """Binds or unbinds the properties of the given ``target`` to the
        properties of this ``OverlayGroup``.

        :arg target: A :class:`.Display` or :class:`.DisplayOpts` instance.

        :arg unbind: Set to ``True`` to bind the properties, ``False`` to
                     unbind them.
        """

        # This is the first overlay to be added - the
        # group should inherit its property values
        if len(self.overlays) == 1:
            master, slave = target, self

        # Other overlays are already in the group - the
        # new overlay should inherit the group properties
        else:
            master, slave = self, target

        bindProps = OverlayGroup._groupBindings.get(target,
                                                    allhits=True,
                                                    bykey=True)

        for clsName, propNames in bindProps.items():
            for propName in propNames:

                groupName = '{}_{}'.format(clsName, propName)

                # If the group property has not yet
                # taken on a value, initialise it
                # to the property value being bound.
                #
                # We do this to avoid clobbering
                # property values with un-initialised
                # group property values.
                if not self.__hasBeenSet[clsName, propName]:
                    setattr(self, groupName, getattr(target, propName))
                    self.__hasBeenSet[clsName, propName] = True

                if slave is self:
                    otherName = propName
                    propName  = groupName
                else:
                    otherName = groupName

                slave.bindProps(propName,
                                master,
                                otherName,
                                bindatt=False,
                                unbind=unbind)


    def __overlayListChanged(self, *a):
        """Called when overlays are added/removed to/from the
        :class:`.OverlayList` . Makes sure that the :attr:`overlays` list for
        this group does not contain any overlays that have been removed.
        """
        for ovl in self.overlays:
            if ovl not in self.__overlayList:
                self.removeOverlay(ovl)


    def __overlayTypeChanged(self, value, valid, display, name):
        """This method is called when the :attr:`.Display.overlayType`
        property for an overlay in the group changes.

        It makes sure that the display properties of the new
        :class:`.DisplayOpts` instance are bound to the group properties.
        """
        opts = display.opts
        self.__bindDisplayOpts(opts)
