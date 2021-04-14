#!/usr/bin/env python
#
# labelgrid.py - the LabelGrid class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LabelGrid` class, which is used
by the :class:`.MelodicClassificationPanel`.
"""


import logging
import collections

import wx

import fsl.data.image             as fslimage
import fsl.utils.idle             as idle

import fsleyes_widgets.widgetgrid as widgetgrid
import fsleyes_widgets.texttag    as texttag

import fsleyes.panel              as fslpanel
import fsleyes.strings            as strings


log = logging.getLogger(__name__)


class LabelGrid(fslpanel.FSLeyesPanel):
    """The ``LabelGrid`` class is the inverse of the :class:`ComponentGrid`.
    It uses a :class:`.WidgetGrid` to display the label-component mappings
    present on the :class:`.VolumeLabels` instance associated with
    an :class:`.Image`. The ``Image`` and ``VolumeLabels`` instances are
    specified via the :meth:`setOverlay` method.

    The grid contains one row for each label, and a :class:`.TextTagPanel` is
    used to display the components associated with each label. Each
    ``TextTagPanel`` allows the user to add and remove components to/from the
    corresponding label.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, lut):
        """Create a ``LabelGrid``.

        :arg parent:      The ``wx`` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg lut:         The :class:`.LookupTable` to be used to colour
                          component tags.
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__lut  = lut
        self.__grid = widgetgrid.WidgetGrid(
            self,
            style=(wx.VSCROLL                    |
                   widgetgrid.WG_SELECTABLE_ROWS |
                   widgetgrid.WG_KEY_NAVIGATION))

        # The LabelGrid displays one TextTagPanel
        # for each label that is currently displayed,
        # as:
        #
        #   { label_name : TextTagPanel }
        #
        # mappings.
        self.__labelTags = collections.OrderedDict()

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)

        self.__grid.Bind(widgetgrid.EVT_WG_SELECT, self.__onGridSelect)

        lut.register(self.name, self.__lutChanged, 'added')
        lut.register(self.name, self.__lutChanged, 'removed')
        lut.register(self.name, self.__lutChanged, 'label')

        self.__overlay = None


    def destroy(self):
        """Must be called when this ``LabelGrid`` is no longer needed.
        De-registers various property listeners, and calls
        :meth:`.FSLeyesPanel.destroy`.
        """

        self.__lut.deregister(self.name, 'added')
        self.__lut.deregister(self.name, 'removed')
        self.__lut.deregister(self.name, 'label')
        self.__lut = None

        self.__deregisterCurrentOverlay()

        fslpanel.FSLeyesPanel.destroy(self)


    def setOverlay(self, overlay, volLabels):
        """Set the :class:`.Image` shown on this ``LabelGrid``. A listener is
        registered with its :class:`.VolumeLabels`, and its component-label
        mappings displayed on the :class:`.WidgetGrid`.
        """

        self.__deregisterCurrentOverlay()
        self.__grid.ClearGrid()
        self.__labelTags.clear()

        if not (isinstance(overlay, fslimage.Image) and
                len(overlay.shape) == 4):
            self.__grid.Refresh()
            return

        log.debug('Registering new overlay: {}'.format(overlay))

        self.__overlay   = overlay
        self.__volLabels = volLabels

        volLabels.register(self.name, self.__labelsChanged)

        # We refresh the label grid on idle, in
        # case multiple calls to setOverlay are
        # made in quick succession - only the most
        # recent request will be executed.
        def createGrid():

            # The grid is initialised with length 0.
            # Rows for each label are are added in
            # the __createTags method, which is called
            # here, and as needed when the LUT or
            # MelodicClassification for the currently
            # selected overlay change.
            self.__grid.SetGridSize(0, 2, [1])
            self.__grid.ShowRowLabels(False)
            self.__grid.ShowColLabels(True)
            self.__grid.SetColLabel(0, strings.labels[self, 'labelColumn'])
            self.__grid.SetColLabel(1, strings.labels[self, 'componentColumn'])

            # The overlay might have been cleared
            # by the time this function gets called
            if self.__overlay is None:
                self.__grid.Refresh()
                return

            self.__createTags()
            self.refreshTags()
            self.__grid.Refresh()

        idle.idle(createGrid,
                  name='{}_createGrid'.format(self.name),
                  skipIfQueued=True)


    def __deregisterCurrentOverlay(self):
        """Called when the selected overlay changes. De-registers property
        listeners associated with the previously selected overlay, if
        necessary.
        """

        if self.__overlay is None:
            return

        volLabels        = self.__volLabels
        self.__overlay   = None
        self.__volLabels = None

        volLabels.deregister(self.name)


    def __createTags(self, labels=None):
        """Makes sure that a :class:`.TextTagPanel` exists for every label
        in the :class:`.LookupTable` and in the :class:`.VolumeLabels`
        for the current overlay.

        :arg labels: If ``None``, this method does what is described above.
                     Otherwise, this must be a list of tuples of
                     ``(name, display name)`` specifying labels which are
                     known not to be present, and for which a ``TextTagPanel``
                     needs to be created.

        :returns: ``True`` if one or more new ``TextTagPanel`` widgets was
                  created (and added to the :class:`.WidgetGrid`), ``False``
                  otherwise.
        """

        # This method should never be called
        # if the current overlay is not set.
        if self.__overlay is None:
            return

        if labels is None:

            volLabels = self.__volLabels
            allLabels = volLabels.getAllLabels()

            # We need to display a row for all
            # the labels from the lut, and all
            # classification labels which are
            # not in the lut.
            lutLabels = [(l.internalName, l.name)
                         for l in self.__lut]
            allLabels = [(l, volLabels.getDisplayLabel(l))
                         for l in allLabels
                         if l not in lutLabels]

            labels = lutLabels + allLabels

        newCreated = False

        log.debug('Creating tag panels for: {}'.format([l[0] for l in labels]))

        # TODO Ensure that there is always
        #      an 'unknown' tag... ?
        for label, displayName in labels:

            # A tag panel already exists for
            # this label, and must therefore
            # already be present in the grid.
            if label in self.__labelTags:
                continue

            newCreated = True
            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_NO_DUPLICATES |
                                               texttag.TTP_KEYBOARD_NAV))

            # This panel is associated with
            # this label - this association
            # will never change, so we can
            # safely store the label on the
            # tag itself, making it easy to
            # figure out the label given a
            # tag object.
            tags._label = displayName

            row = self.__grid.GetGridSize()[0]
            self.__grid.InsertRow(row)
            self.__grid.SetText(  row, 0, displayName)
            self.__grid.SetWidget(row, 1, tags)

            self.__labelTags[label] = tags

            tags.Bind(texttag.EVT_TTP_TAG_ADDED,   self.__onTagAdded)
            tags.Bind(texttag.EVT_TTP_TAG_REMOVED, self.__onTagRemoved)
            tags.Bind(texttag.EVT_TTP_TAG_SELECT,  self.__onTagSelect)

        return newCreated


    def refreshTags(self, labels=None):
        """Makes sure that the tags shown on each :class:`.TextTagPanel`
        are consistent with respect to the current state of the
        :class:`.VolumeLabels`.

        :arg labels: Labels to refresh. If ``None``, the tags for every
                     displayed label is refreshed.
        """

        if labels is None:
            labels = list(self.__labelTags.keys())

        log.debug('Refreshing tags for {}'.format(labels))

        # This method should never be called
        # if the current overlay is not set.
        lut       = self.__lut
        volLabels = self.__volLabels
        numComps  = volLabels.numComponents()
        compStrs  = [str(i) for i in range(1, numComps + 1)]

        for label in labels:

            tags     = self.__labelTags[label]
            lutLabel = lut.getByName(label)

            comps = volLabels.getComponents(label)

            # This is a label which is not in the
            # LUT. If we set colour to None, the
            # TextTagPanel will use a random colour.
            if lutLabel is None:
                colour = None

            # If this label is in the LUT, use
            # the colour associated with it.
            else:
                colour = lutLabel.colour
                colour = [int(round(c  * 255.0)) for c in colour]

            tags.ClearTags()
            tags.SetOptions(compStrs, [colour] * len(compStrs))

            for comp in comps:
                tags.AddTag(str(comp + 1))


    def __onGridSelect(self, ev):
        """Called when a row is selected in the :class:`.WidgetGrid`. Makes
        sure that  the first tag in the :class:`.TextTagPanel` has the focus.
        """

        tags = self.__grid.GetWidget(ev.row, 1)

        log.debug('Grid row selected (label "{}")'.format(tags._label))

        tags.FocusNewTagCtrl()


    def __onTagAdded(self, ev):
        """Called when a tag is added to a :class:`.TextTagPanel`. Adds
        the corresponding label-component mapping to the
        :class:`.VolumeLabels` instance.
        """

        tags      = ev.GetEventObject()
        volLabels = self.__volLabels
        comp      = int(ev.tag) - 1
        label     = tags._label

        log.debug('Component {} added to label {}'.format(comp, label))

        with volLabels.skip(self.name):

            # If this component now has two
            # labels, and the other label is
            # 'Unknown', remove the 'Unknown'
            # label.
            if len(volLabels.getLabels(comp)) == 1 and \
               label != 'unknown'                  and \
               volLabels.hasLabel(comp, 'unknown'):

                log.debug('Removing component {} from '
                          '"unknown" tag'.format(comp))

                volLabels.removeLabel(comp, 'unknown')
                self.__labelTags['unknown'].RemoveTag(str(comp + 1))

            volLabels.addComponent(label, comp)

        # The WidgetGrid doesn't
        # resize itself when its
        # contents change size
        self.__grid.Layout()


    def __onTagRemoved(self, ev):
        """Called when a tag is removed from a :class:`.TextTagPanel`. Removes
        the corresponding label-component mapping from the
        :class:`.VolumeLabels` instance.
        """

        tags      = ev.GetEventObject()
        volLabels = self.__volLabels
        lut       = self.__lut
        comp      = int(ev.tag) - 1
        label     = tags._label

        log.debug('Component {} removed from label {}'.format(comp, label))

        with volLabels.skip(self.name):

            volLabels.removeComponent(label, comp)

            # If the component has no more labels,
            # give it an 'Unknown' label
            if len(volLabels.getLabels(comp)) == 0:

                # What if there is no 'unknown'
                # entry in labelTags? Add it?
                label = lut.getByName('unknown')
                tags  = self.__labelTags['unknown']

                if label is None: name = volLabels.getDisplayLabel('unknown')
                else:             name = label.name

                # There should always be an 'unknown'
                # label in the LUT, but just in case.
                if label is None:
                    colour = None
                else:
                    colour = [int(round(c * 255.0)) for c in label.colour]

                log.debug('Adding component {} to '
                          '"unknown" tag'.format(comp))

                volLabels.addLabel(comp, name)
                tags.AddTag(str(comp + 1), colour)

        # The WidgetGrid doesn't
        # resize itself when its
        # contents change size
        self.__grid.Layout()


    def __onTagSelect(self, ev):
        """Called when a tag from a :class:`.TextTagPanel` is selected.
        Changes the current :attr:`.NiftiOpts.volume` to the component
        corresponding to the selected tag.
        """

        comp        = int(ev.tag) - 1
        overlay     = self.__overlay
        opts        = self.displayCtx.getOpts(overlay)

        log.debug('Component {} selected on label grid - '
                  'updating overlay volume'.format(comp))

        opts.volume = comp


    def __lutChanged(self, lut, topic, value):
        """Called when the :class:`.LookupTable` changes. Adds/removes/updates
        the displayed labels as needed.
        """

        if self.__overlay is None:
            return

        # The LookupTable passes us the LutLabel
        # object and its index in the LUT
        label, idx = value
        volLabels  = self.__volLabels

        # A label has been removed
        if topic == 'removed':

            # Delete the corresponding row
            # in the grid if there are no
            # components with the deleted
            # label.
            tags = self.__labelTags.get(label.internalName, None)

            if tags is not None and \
               len(volLabels.getComponents(label.internalName)) == 0:

                row = self.__grid.GetRow(tags)

                log.debug('LUT label {} removed - removing '
                          'corresponding row ({}) from widget '
                          'grid'.format(label.internalName, row))

                self.__labelTags.pop(label.internalName)
                self.__grid.DeleteRow(row)
                self.__grid.Layout()

        # A label has been added
        elif topic == 'added':

            # Are we already displaying a
            # label/tag which corresponds
            # to the new LUT label?
            tags = self.__labelTags.get(label.internalName, None)

            # If so, update its
            # colours, and return
            if tags is not None:
                colour = [int(round(c * 255.0)) for c in label.colour]

                for tag in tags.GetTags() + tags.GetOptions():
                    tags.SetTagColour(tag, colour)

            # Otherwise this is a new tag.
            # Create a tag/grid row for it
            else:
                self.__createTags([(label.internalName, label.name)])
                self.refreshTags(  [label.internalName])
                self.__grid.Refresh()

        # A property (name, colour) of an
        # existing label has changed.
        elif topic == 'label':

            # The only lut property that we track is
            # the label colour. If the label name
            # changes, we will ignore it; it will
            # ultimately be treated as a new label.
            tags = self.__labelTags.get(label.internalName, None)

            if tags is not None:
                colour = [int(round(c * 255.0)) for c in label.colour]

                for tag in tags.GetTags() + tags.GetOptions():
                    tags.SetTagColour(tag, colour)


    def __labelsChanged(self, volLabels, topic, components):
        """Called when the labels in the :class:`.VolumeLabels`
        associated with the current overlay change. Updates the displayed
        tags.
        """

        log.debug('Volume label changed - refreshing label grid tags')

        added = topic == 'added'

        for comp, label in components:
            tags = self.__labelTags.get(label, None)

            # Existing label
            if tags is not None:
                if added: tags.AddTag(   str(comp + 1))
                else:     tags.RemoveTag(str(comp + 1))

            # New label
            else:
                displayName = volLabels.getDisplayLabel(label)
                self.__createTags([(label, displayName)])
                self.refreshTags(  [label])
                self.__grid.Refresh()
