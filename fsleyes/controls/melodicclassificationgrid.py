#!/usr/bin/env python
#
# melodicclassificationgrid.py - the ComponentGrid and LabelGrid classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ComponentGrid` and :class:`LabelGrid`
classes, which are used by the :class:`.MelodicClassificationPanel`.
"""


import logging

import wx

import pwidgets.widgetgrid        as widgetgrid
import pwidgets.texttag           as texttag

import fsl.fsleyes.panel          as fslpanel
import fsl.fsleyes.strings        as strings
import fsl.fsleyes.displaycontext as fsldisplay
import fsl.data.melodicimage      as fslmelimage


log = logging.getLogger(__name__)


class ComponentGrid(fslpanel.FSLEyesPanel):
    """The ``ComponentGrid`` uses a :class:`.WidgetGrid`, and a set of
    :class:`.TextTagPanel` widgets, to display the component classifications
    stored in the :class:`.MelodicClassification` object that is associated
    with a :class:`.MelodicImage`. The ``MelodicImage`` is specified via
    the :meth:`setOverlay` method.

    The grid contains one row for each component, and a ``TextTagPanel`` is
    used to display the labels associated with each component. Each
    ``TextTagPanel`` allows the user to add and remove labels to/from the
    corresponding component.
    """

    
    def __init__(self, parent, overlayList, displayCtx, lut):
        """Create a ``ComponentGrid``.

        :arg parent:      The ``wx`` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg lut:         The :class:`.LookupTable` instance used to colour
                          each label tag.
        """
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

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

        lut.addListener('labels', self._name, self.__lutChanged)

        self.__overlay = None

        
    def destroy(self):
        """Must be called when this ``ComponentGrid`` is no longer needed.
        De-registers various property listeners, and calls
        :meth:`.FSLEyesPanel.destroy`.
        """
        
        self.__lut.removeListener('labels', self._name)
        self.__deregisterCurrentOverlay()
        
        self.__lut = None

        fslpanel.FSLEyesPanel.destroy(self)

        
    def setOverlay(self, overlay):
        """Sets the :class:`.MelodicImage` to display component labels for.
        The :class:`.WidgetGrid` is re-populated to display the
        component-label mappings contained in the
        :class:`.MelodicClassification` instance associated with the overlay..
        """

        self.__deregisterCurrentOverlay()
        self.__grid.ClearGrid()
        self.__grid.Refresh()

        if not isinstance(overlay, fslmelimage.MelodicImage):
            return

        self.__overlay = overlay
        display        = self._displayCtx.getDisplay(overlay)
        opts           = display.getDisplayOpts()
        melclass       = overlay.getICClassification()
        ncomps         = overlay.numComponents()
        
        self.__grid.SetGridSize(ncomps, 2, growCols=[1])

        self.__grid.SetColLabel(0, strings.labels[self, 'componentColumn'])
        self.__grid.SetColLabel(1, strings.labels[self, 'labelColumn'])

        opts    .addListener('volume', self._name, self.__volumeChanged)
        melclass.addListener('labels', self._name, self.__labelsChanged)
        display .addListener('overlayType',
                             self._name,
                             self.__overlayTypeChanged)
        
        self.__recreateTags()
        self.__volumeChanged()


    def __deregisterCurrentOverlay(self):
        """Called when the selected overlay changes. De-registers listeners
        associated with the previously selected overlay, if necessary.
        """

        if self.__overlay is None:
            return

        overlay        = self.__overlay
        self.__overlay = None
        
        melclass = overlay.getICClassification()
        melclass.removeListener('labels', self._name)
            
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
        self.setOverlay(self.__overlay)

        
    def __recreateTags(self):
        """Re-creates a :class:`.TextTagPanel` for every component in the
        :class:`.MelodicImage`.
        """

        overlay  = self.__overlay
        numComps = overlay.numComponents()

        for i in range(numComps):

            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_ALLOW_NEW_TAGS |
                                               texttag.TTP_NO_DUPLICATES  |
                                               texttag.TTP_KEYBOARD_NAV))

            # Store the component number on the tag
            # panel, so we know which component we
            # are dealing with in the __onTagAdded
            # and __onTagRemoved methods.
            tags._melodicComponent = i

            self.__grid.SetText(  i, 0, str(i + 1))
            self.__grid.SetWidget(i, 1, tags)

            tags.Bind(texttag.EVT_TTP_TAG_ADDED,   self.__onTagAdded)
            tags.Bind(texttag.EVT_TTP_TAG_REMOVED, self.__onTagRemoved)

        self.__grid.Refresh()

        self.__refreshTagOptions()
        self.__refreshTags()

        self.Layout()


    def __refreshTagOptions(self):
        """Updates the options available on each :class:`.TextTagPanel`, from
        the entries in the melodic classification :class:`.LookupTable`.
        """

        overlay  = self.__overlay
        numComps = overlay.numComponents() 
        
        lut           = self.__lut
        displayLabels = [l.displayName() for l in lut.labels]
        colours       = [l.colour()      for l in lut.labels]

        for i in range(len(colours)):
            colours[i] = [int(round(c * 255)) for c in colours[i]] 
        
        for comp in range(numComps):
            tags = self.__grid.GetWidget(comp, 1)
            tags.SetOptions(displayLabels, colours) 


    def __refreshTags(self):
        """Re-generates the tags on every :class:`.TextTagPanel` in the grid.
        """ 
        
        overlay  = self.__overlay
        melclass = overlay.getICClassification()
        numComps = overlay.numComponents() 

        for row in range(numComps):
            
            tags = self.__grid.GetWidget(row, 1)

            tags.ClearTags()

            for label in melclass.getLabels(row):
                tags.AddTag(melclass.getDisplayLabel(label))

        self.__grid.FitInside()


    def __onTagAdded(self, ev):
        """Called when a tag is added to a :class:`.TextTagPanel`. Adds the
        corresponding component-label mapping to the
        :class:`.MelodicClassification` instance.
        """

        tags     = ev.GetEventObject()
        label    = ev.tag
        comp     = tags._melodicComponent
        overlay  = self.__overlay
        lut      = self.__lut 
        melclass = overlay.getICClassification()

        log.debug('Label added to component {} ("{}")'.format(comp, label))

        # Add the new label to the melodic component
        melclass.disableListener(    'labels', self._name)
        melclass.disableNotification('labels')
        
        melclass.addLabel(comp, label)

        # If the tag panel previously just contained
        # the 'Unknown' tag, remove that tag
        if tags.TagCount() == 2   and \
           tags.HasTag('Unknown') and \
           label.lower() != 'unknown':
            melclass.removeLabel(comp, 'Unknown')
            tags.RemoveTag('Unknown')

        melclass.enableNotification('labels')
        melclass.notify(            'labels')
        melclass.enableListener(    'labels', self._name)

        # If the newly added tag is not in
        # the lookup table, add it in
        if lut.getByName(label) is None:
            colour = tags.GetTagColour(label)
            colour = [c / 255.0 for c in colour]

            log.debug('Adding new lookup table '
                      'entry for label {}'.format(label))

            lut.disableListener('labels', self._name)
            lut.new(name=label, colour=colour)
            lut.enableListener('labels', self._name)

        self.__refreshTagOptions()
        self.__grid.FitInside()

        
    def __onTagRemoved(self, ev):
        """Called when a tag is removed from a :class:`.TextTagPanel`.
        Removes the corresponding component-label mapping from the
        :class:`.MelodicClassification` instance.
        """ 
        
        tags     = ev.GetEventObject()
        label    = ev.tag
        comp     = tags._melodicComponent
        overlay  = self.__overlay
        melclass = overlay.getICClassification()

        log.debug('Label removed from component {} ("{}")'.format(comp, label))

        # Remove the label from
        # the melodic component
        melclass.disableListener(    'labels', self._name)
        melclass.disableNotification('labels')
        
        melclass.removeLabel(comp, label)

        # If the tag panel now has no tags,
        # add the 'Unknown' tag back in.
        if len(melclass.getLabels(comp)) == 0:
            melclass.addLabel(comp, 'Unknown')
            tags.AddTag('Unknown')

        melclass.enableNotification('labels')
        melclass.notify(            'labels')
        melclass.enableListener(    'labels', self._name)

        self.__grid.FitInside()


    def __onGridSelect(self, ev):
        """Called when a row is selected on the :class:`.WidgetGrid`. Makes
        sure that the 'new tag' control in the corresponding
        :class:`.TextTagPanel` is focused.
        """

        component = ev.row
        opts      = self._displayCtx.getOpts(self.__overlay)

        log.debug('Grid row selected (component {})'.format(component))

        opts.disableListener('volume', self._name)
        opts.volume = component
        opts.enableListener('volume', self._name)

        tags = self.__grid.GetWidget(ev.row, 1)
        tags.FocusNewTagCtrl()


    def __volumeChanged(self, *a):
        """Called when the :attr:`.Nifti1Opts.volume` property changes. Selects
        the corresponding row in the :class:`.WidgetGrid`.
        """

        # Only change the row if we are
        # currently visible, otherwise
        # this will screw up the focus.
        if not self.IsShown():
            return

        grid = self.__grid
        opts = self._displayCtx.getOpts(self.__overlay)

        log.debug('Overlay volume changed ({})'.format(opts.volume))
 
        grid.SetSelection(opts.volume, -1)


    def __labelsChanged(self, *a):
        """Called when the :attr:`.MelodicClassification.labels` change.
        Re-generates the tags shown on every :class:`.TextTagPanel`.
        """
        log.debug('Melodic classification changed - '
                  'refreshing component grid tags')
        self.__refreshTags()


    def __lutChanged(self, *a):
        """Called when the :attr:`.LookupTable.labels` change.
        Updates the options on every :class:`.TextTagPanel`.
        """
        log.debug('Lookup table changed - refreshing '
                  'component grid tag options')
        self.__refreshTagOptions()


class LabelGrid(fslpanel.FSLEyesPanel):
    """The ``LabelGrid`` class is the inverse of the :class:`ComponentGrid`.
    It uses a :class:`.WidgetGrid` to display the label-component mappings
    present on the :class:`.MelodicClassification` instance associated with
    a :class:`.MelodicImage`. The ``MelodicImage`` is specified via
    the :meth:`setOverlay` method.

    The grid contains one row for each label, and a :class:`.TextTagPanel` is
    used to display the components associated with each label. Each
    ``TextTagPanel`` allows the user to add and remove components to/from the
    corresponding label.
    """

    
    def __init__(self, parent, overlayList, displayCtx, lut):
        """Create a ``LabelGrid``.

        :arg parent:      The ``wx`` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg lut:         The :class:`.LookupTable` to be used to colour
                          component tags.
        """
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

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

        lut.addListener('labels', self._name, self.__lutChanged)

        self.__overlay = None
        self.__recreateGrid()

        
    def destroy(self):
        """Must be called when this ``LabelGrid`` is no longer needed.
        De-registers various property listeners, and calls
        :meth:`.FSLEyesPanel.destroy`.
        """
        
        self.__lut.removeListener('labels', self._name)
        self.__deregisterCurrentOverlay()
        
        self.__lut = None

        fslpanel.FSLEyesPanel.destroy(self)


    def setOverlay(self, overlay):
        """Set the :class:`.MelodicImage` shown on this ``LabelGrid``. A
        listener is registered with its :class:`.MelodicClassification`,
        and its component-label mappings displayed on the
        :class:`.WidgetGrid`.
        """

        self.__deregisterCurrentOverlay()

        overlay = self._displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslmelimage.MelodicImage):
            return

        self.__overlay = overlay
        melclass       = overlay.getICClassification()

        melclass.addListener('labels', self._name, self.__labelsChanged)

        self.__refreshTags()

        
    def __deregisterCurrentOverlay(self):
        """Called when the selected overlay changes. De-registers property
        listeners associated with the previously selected overlay, if
        necessary.
        """

        if self.__overlay is None:
            return

        overlay        = self.__overlay
        self.__overlay = None
        
        melclass = overlay.getICClassification()
        melclass.removeListener('labels', self._name)


    def __recreateGrid(self):
        """Clears the :class:`.WidgetGrid`, and re-creates
        a :class:`.TextTagPanel` for every available melodic classification
        label.
        """

        grid   = self.__grid
        lut    = self.__lut
        labels = lut.labels
        
        grid.ClearGrid()

        grid.SetGridSize(len(labels), 2, growCols=[1])

        grid.SetColLabel(0, strings.labels[self, 'labelColumn'])
        grid.SetColLabel(1, strings.labels[self, 'componentColumn'])

        for i, label in enumerate(labels):
            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_NO_DUPLICATES |
                                               texttag.TTP_KEYBOARD_NAV))

            tags._label = label.name()

            self.__grid.SetText(  i, 0, label.displayName())
            self.__grid.SetWidget(i, 1, tags)
            
            tags.Bind(texttag.EVT_TTP_TAG_ADDED,   self.__onTagAdded)
            tags.Bind(texttag.EVT_TTP_TAG_REMOVED, self.__onTagRemoved)
            tags.Bind(texttag.EVT_TTP_TAG_SELECT,  self.__onTagSelect)

        self.__grid.Refresh()


    def __refreshTags(self):
        """Re-populates the label-component mappings shown on the
        :class:`.TextTagPanel` widgets in the :class:`.WidgetGrid`.
        """

        lut      = self.__lut
        grid     = self.__grid
        overlay  = self.__overlay
        numComps = overlay.numComponents()
        melclass = overlay.getICClassification()

        for i, label in enumerate(lut.labels):

            tags  = grid.GetWidget(i, 1)
            comps = melclass.getComponents(label.name())
            
            tags.ClearTags()

            tags.SetOptions(map(str, range(1, numComps + 1)))

            for comp in comps:

                colour = label.colour()
                colour = [int(round(c  * 255.0)) for c in colour]
                tags.AddTag(str(comp + 1), colour)

        self.__grid.Layout()

                
    def __onTagAdded(self, ev):
        """Called when a tag is added to a :class:`.TextTagPanel`. Adds
        the corresponding label-component mapping to the
        :class:`.MelodicClassification` instance.
        """ 

        tags     = ev.GetEventObject()
        overlay  = self.__overlay
        melclass = overlay.getICClassification()
        comp     = int(ev.tag) - 1
        label    = tags._label

        log.debug('Component added to label {} ({})'.format(label, comp)) 

        melclass.disableListener(    'labels', self._name)
        melclass.disableNotification('labels')

        # If this component now has two labels, and
        # the other label is 'Unknown', remove the
        # 'Unknown' label.
        if len(melclass.getLabels(comp)) == 1 and \
           label != 'unknown'                 and \
           melclass.hasLabel(comp, 'unknown'):
            melclass.removeLabel(comp, 'unknown')
        
        melclass.addComponent(label, comp)

        melclass.enableNotification('labels')
        melclass.notify(            'labels')
        melclass.enableListener(    'labels', self._name)
        
        self.__refreshTags()

    
    def __onTagRemoved(self, ev):
        """Called when a tag is removed from a :class:`.TextTagPanel`. Removes
        the corresponding label-component mapping from the
        :class:`.MelodicClassification` instance.
        """
        
        tags     = ev.GetEventObject()
        overlay  = self.__overlay
        melclass = overlay.getICClassification()
        comp     = int(ev.tag) - 1
        label    = tags._label

        log.debug('Component removed from label {} ({})'.format(label, comp))

        melclass.disableListener(    'labels', self._name)
        melclass.disableNotification('labels')
        
        melclass.removeComponent(label, comp)

        # If the component has no more labels,
        # give it an 'Unknown' label
        if len(melclass.getLabels(comp)) == 0:
            melclass.addLabel(comp, 'Unknown')

        melclass.enableNotification('labels')
        melclass.notify(            'labels')
        melclass.enableListener(    'labels', self._name) 
        self.__refreshTags()


    def __onGridSelect(self, ev):
        """Called when a row is selected in the :class:`.WidgetGrid`. Makes
        sure that  the first tag in the :class:`.TextTagPanel` has the focus.
        """

        tags = self.__grid.GetWidget(ev.row, 1)

        log.debug('Grid row selected (label "{}")'.format(tags._label))
        
        tags.FocusNewTagCtrl()


    def __onTagSelect(self, ev):
        """Called when a tag from a :class:`.TextTagPanel` is selected.
        Changes the current :attr:`.Nifti1Opts.volume` to the component
        corresponding to the selected tag.
        """

        comp        = int(ev.tag) - 1
        overlay     = self.__overlay
        opts        = self._displayCtx.getOpts(overlay)

        log.debug('Tag selected on label grid: component {}'.format(comp))
        
        opts.volume = comp
       

    def __lutChanged(self, *a):
        """Called when the :attr:`LookupTable.labels` change. Re-creates and
        re-populates the :class:`.WidgetGrid`.
        """
        log.debug('Lookup table changed - re-creating label grid')
        self.__recreateGrid()
        self.__refreshTags()

        
    def __labelsChanged(self, *a):
        """Called when the :attr:`.MelodicClassification.labels` change.
        Re-populates the :class:`.WidgetGrid`.
        """
        log.debug('Melodic classification changed - '
                  'refreshing label grid tags')
        self.__refreshTags()
