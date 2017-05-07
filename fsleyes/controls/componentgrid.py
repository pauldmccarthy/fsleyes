#!/usr/bin/env python
#
# componentgrid.py - the ComponentGrid class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ComponentGrid` class, which is used by
the :class:`.MelodicClassificationPanel`.
"""


import logging

import wx

import fsl.data.image             as fslimage
import fsl.utils.async            as async

import fsleyes_props              as props
import fsleyes_widgets.widgetgrid as widgetgrid
import fsleyes_widgets.texttag    as texttag
import fsleyes.panel              as fslpanel
import fsleyes.strings            as strings
import fsleyes.displaycontext     as fsldisplay


log = logging.getLogger(__name__)


class ComponentGrid(fslpanel.FSLeyesPanel):
    """The ``ComponentGrid`` uses a :class:`.WidgetGrid`, and a set of
    :class:`.TextTagPanel` widgets, to display the component classifications
    stored in the :class:`.VolumeLabels` object that is associated
    with an :class:`.Image` (typically a :class:`.MelodicImage`). The
    ``Image`` and ``VolumeLabels`` instance is specified via the
    :meth:`setOverlay` method.


    The grid contains one row for each component, and a ``TextTagPanel`` is
    used to display the labels associated with each component. Each
    ``TextTagPanel`` allows the user to add and remove labels to/from the
    corresponding component.


    See also the :class:`.LabelGrid` class, which displays the same
    information, but organised by label.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, lut):
        """Create a ``ComponentGrid``.

        :arg parent:      The ``wx`` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg lut:         The :class:`.LookupTable` instance used to colour
                          each label tag.
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__lut  = lut
        self.__grid = widgetgrid.WidgetGrid(
            self,
            style=(wx.VSCROLL                    |
                   widgetgrid.WG_SELECTABLE_ROWS |
                   widgetgrid.WG_KEY_NAVIGATION))

        self.__grid.ShowRowLabels(False)
        self.__grid.ShowColLabels(True)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)

        self.__grid.Bind(widgetgrid.EVT_WG_SELECT, self.__onGridSelect)

        lut.register(self._name, self.__lutChanged, 'added')
        lut.register(self._name, self.__lutChanged, 'removed')
        lut.register(self._name, self.__lutChanged, 'label')

        self.__overlay   = None
        self.__volLabels = None


    def destroy(self):
        """Must be called when this ``ComponentGrid`` is no longer needed.
        De-registers various property listeners, and calls
        :meth:`.FSLeyesPanel.destroy`.
        """

        self.__lut.deregister(self._name, 'added')
        self.__lut.deregister(self._name, 'removed')
        self.__lut.deregister(self._name, 'label')
        self.__deregisterCurrentOverlay()

        self.__lut = None

        fslpanel.FSLeyesPanel.destroy(self)


    def setOverlay(self, overlay, volLabels, refreshGrid=True):
        """Sets the :class:`.Image` to display component labels for.
        The :class:`.WidgetGrid` is re-populated to display the
        component-label mappings contained in the
        :class:`.VolumeLabels` instance associated with the overlay.

        :arg refreshGrid: If ``True`` (the default), the ``WidgetGrid``
                          displaying component labels is refreshed. This
                          flag is used internally (see
                          :meth:`__overlayTypeChanged`).
        """

        self.__deregisterCurrentOverlay()
        self.__grid.ClearGrid()

        if not (isinstance(overlay, fslimage.Image) and
                len(overlay.shape) == 4):
            self.__grid.Refresh()
            return

        log.debug('Registering new overlay: {}'.format(overlay))

        self.__overlay   = overlay
        self.__volLabels = volLabels
        display          = self._displayCtx.getDisplay(overlay)
        opts             = display.getDisplayOpts()
        ncomps           = volLabels.numComponents()

        volLabels.register(             self._name, self.__labelsChanged)
        opts     .addListener('volume', self._name, self.__volumeChanged)
        display  .addListener('overlayType',
                              self._name,
                              self.__overlayTypeChanged)

        # We refresh the component grid on idle, in
        # case multiple calls to setOverlay are made
        # in quick succession - only the most recent
        # request will be executed.
        def doRefreshGrid():

            # The overlay might have been cleared
            # by the time this function gets called
            if self.__overlay is None:
                self.__grid.Refresh()
                return

            self.__grid.SetGridSize(ncomps, 2, growCols=[1])

            self.__grid.SetColLabel(0, strings.labels[self, 'componentColumn'])
            self.__grid.SetColLabel(1, strings.labels[self, 'labelColumn'])

            self.__recreateTags()
            self.__volumeChanged()

        if refreshGrid:
            async.idle(doRefreshGrid,
                       name='{}_doRefreshGrid'.format(self._name),
                       skipIfQueued=True)


    def refreshTags(self, comps=None):
        """Clears and refreshes the tags on every :class:`.TextTagPanel` in
        the grid.

        :arg comps: Components to refresh. If ``None``, the tags for all
                    components are refreshed.
        """

        overlay   = self.__overlay
        volLabels = self.__volLabels
        numComps  = volLabels.numComponents()

        if comps is None:
            comps = list(range(numComps))

        if len(comps) == 0:
            return

        log.debug('Refreshing tags for {} [{}, ..., {}]'.format(
            overlay, comps[0], comps[-1]))

        for row in comps:

            tags = self.__grid.GetWidget(row, 1)

            tags.ClearTags()

            for label in volLabels.getLabels(row):
                tags.AddTag(volLabels.getDisplayLabel(label))

        self.__grid.Layout()


    def __deregisterCurrentOverlay(self):
        """Called when the selected overlay changes. De-registers listeners
        associated with the previously selected overlay, if necessary.
        """

        if self.__overlay is None:
            return

        overlay          = self.__overlay
        volLabels        = self.__volLabels
        self.__overlay   = None
        self.__volLabels = None

        volLabels.deregister(self._name)

        try:
            display = self._displayCtx.getDisplay(overlay)
            opts    = display.getDisplayOpts()
            opts   .removeListener('volume',      self._name)
            display.removeListener('overlayType', self._name)

        except fsldisplay.InvalidOverlayError:
            pass


    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` of the currently
        displayed overlay changes. When the type of an overlay changes,
        a new :class:`.DisplayOpts` instance is created, so we need to
        re-register various property listeners with this new
        ``DisplayOpts`` instance.
        """
        self.setOverlay(self.__overlay, refreshGrid=False)


    def __recreateTags(self):
        """Called by :meth:`setOverlay`. Re-creates a :class:`.TextTagPanel`
        for every component in the :class:`.Image`.
        """

        volLabels = self.__volLabels
        numComps  = volLabels.numComponents()

        for i in range(numComps):

            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_ALLOW_NEW_TAGS |
                                               texttag.TTP_NO_DUPLICATES  |
                                               texttag.TTP_KEYBOARD_NAV))

            # Store the component number on the tag
            # panel, so we know which component we
            # are dealing with in the __onTagAdded
            # and __onTagRemoved methods.
            tags._componentIndex = i

            self.__grid.SetText(  i, 0, str(i + 1))
            self.__grid.SetWidget(i, 1, tags)

            tags.Bind(texttag.EVT_TTP_TAG_ADDED,   self.__onTagAdded)
            tags.Bind(texttag.EVT_TTP_TAG_REMOVED, self.__onTagRemoved)

        self.__grid.Refresh()
        self.__refreshTagOptions()
        self.refreshTags()
        self.Layout()


    def __refreshTagOptions(self):
        """Updates the options available on each :class:`.TextTagPanel`, from
        the entries in the melodic classification :class:`.LookupTable`.
        """

        overlay   = self.__overlay
        volLabels = self.__volLabels
        numComps  = volLabels.numComponents()

        log.debug('Updating component tag options for {}'.format(overlay))

        lut     = self.__lut
        labels  = [l.name   for l in lut]
        colours = [l.colour for l in lut]

        for i in range(len(colours)):
            colours[i] = [int(round(c * 255)) for c in colours[i]]

        for comp in range(numComps):
            tags = self.__grid.GetWidget(comp, 1)
            tags.SetOptions(labels, colours)


    def __onTagAdded(self, ev):
        """Called when a tag is added to a :class:`.TextTagPanel`. Adds the
        corresponding component-label mapping to the
        :class:`.VolumeLabels` instance.
        """

        tags      = ev.GetEventObject()
        label     = ev.tag
        comp      = tags._componentIndex
        lut       = self.__lut
        volLabels = self.__volLabels

        log.debug('Label added to component {} ("{}")'.format(comp, label))

        # Add the new label to the component
        with volLabels.skip(self._name):

            volLabels.addLabel(comp, label)

            # If the tag panel previously just contained
            # the 'Unknown' tag, remove that tag
            if tags.TagCount() == 2   and \
               tags.HasTag('Unknown') and \
               label.lower() != 'unknown':

                log.debug('Removing "unknown" tag from '
                          'component {}'.format(comp))

                volLabels.removeLabel(comp, 'Unknown')
                tags.RemoveTag('Unknown')

        # If the newly added tag is not in
        # the lookup table, add it in
        if lut.getByName(label) is None:
            colour = tags.GetTagColour(label)
            colour = [c / 255.0 for c in colour]

            log.debug('Adding new lookup table '
                      'entry for label {}'.format(label))

            with lut.skip(self._name, ('added', 'removed', 'label')):
                lut.new(name=label, colour=colour)

            self.__refreshTagOptions()
        self.__grid.Layout()


    def __onTagRemoved(self, ev):
        """Called when a tag is removed from a :class:`.TextTagPanel`.
        Removes the corresponding component-label mapping from the
        :class:`.VolumeLabels` instance.
        """

        tags      = ev.GetEventObject()
        label     = ev.tag
        comp      = tags._componentIndex
        volLabels = self.__volLabels

        log.debug('Label removed from component {} ("{}")'.format(comp, label))

        # Remove the label from
        # the melodic component
        with volLabels.skip(self._name):

            volLabels.removeLabel(comp, label)

            # If the tag panel now has no tags,
            # add the 'Unknown' tag back in.
            if len(volLabels.getLabels(comp)) == 0:

                log.debug('Adding "unknown" tag to '
                          'component {}'.format(comp))

                volLabels.addLabel(comp, 'Unknown')
                tags.AddTag('Unknown')

        self.__grid.FitInside()


    def __onGridSelect(self, ev):
        """Called when a row is selected on the :class:`.WidgetGrid`. Makes
        sure that the 'new tag' control in the corresponding
        :class:`.TextTagPanel` is focused.
        """

        component = ev.row
        opts      = self._displayCtx.getOpts(self.__overlay)

        log.debug('Grid row selected (component {}) - updating '
                  'overlay volume'.format(component))

        with props.skip(opts, 'volume', self._name):
            opts.volume = component

        tags = self.__grid.GetWidget(ev.row, 1)
        tags.FocusNewTagCtrl()


    def __volumeChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` property changes. Selects
        the corresponding row in the :class:`.WidgetGrid`.
        """

        # Only change the row if we are
        # currently visible, otherwise
        # this will screw up the focus.
        if not self.IsShown():
            return

        grid = self.__grid
        opts = self._displayCtx.getOpts(self.__overlay)

        log.debug('Overlay volume changed ({}) - updating '
                  'selected component'.format(opts.volume))

        grid.SetSelection(opts.volume, -1)


    def __labelsChanged(self, volLabels, topic, components):
        """Called on :class:`.VolumeLabels` notifications.
        Re-generates the tags shown on every :class:`.TextTagPanel`.
        """

        log.debug('Volume labels changed - '
                  'refreshing component grid tags')

        # The MelodicClassification
        # passes (component, label)
        # tuples, but we only care
        # about the components
        components = [c[0] for c in components]
        self.refreshTags(components)


    def __lutChanged(self, *a):
        """Called when the :attr:`.LookupTable.labels` change.
        Updates the options on every :class:`.TextTagPanel`.
        """
        log.debug('Lookup table changed - refreshing '
                  'component grid tag options')

        self.__refreshTagOptions()
