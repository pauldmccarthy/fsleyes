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

import wx

import props

import pwidgets.widgetgrid    as widgetgrid
import pwidgets.texttag       as texttag

import fsl.data.melodicimage  as fslmelimage
import fsl.utils.async        as async

import fsleyes.panel          as fslpanel
import fsleyes.strings        as strings
import fsleyes.displaycontext as fsldisplay


log = logging.getLogger(__name__)


class LabelGrid(fslpanel.FSLeyesPanel):
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
        
        fslpanel.FSLeyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__lut  = lut
        self.__grid = widgetgrid.WidgetGrid(
            self,
            style=(wx.VSCROLL                    |
                   widgetgrid.WG_SELECTABLE_ROWS |
                   widgetgrid.WG_KEY_NAVIGATION))

        self.__grid.ShowRowLabels(False)
        self.__grid.ShowColLabels(True)

        # The LabelGrid displays one TextTagPanel
        # for each label that is currently displayed,
        # as:
        # 
        #   { label_name : TextTagPanel }
        # 
        # mappings
        self.__tagMap = {}

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)
        
        self.SetSizer(self.__sizer)

        self.__grid.Bind(widgetgrid.EVT_WG_SELECT, self.__onGridSelect)

        lut.register(self._name, self.__lutChanged, 'added') 
        lut.register(self._name, self.__lutChanged, 'removed')
        lut.register(self._name, self.__lutChanged, 'label')

        self.__overlay = None
        self.__recreateGrid()

        
    def destroy(self):
        """Must be called when this ``LabelGrid`` is no longer needed.
        De-registers various property listeners, and calls
        :meth:`.FSLeyesPanel.destroy`.
        """
        
        self.__lut.deregister(self._name, 'added')
        self.__lut.deregister(self._name, 'removed')
        self.__lut.deregister(self._name, 'label')
        self.__deregisterCurrentOverlay()
        
        self.__lut = None

        fslpanel.FSLeyesPanel.destroy(self)


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

        melclass.register(self._name, self.__labelsChanged)

        self.__refreshTags()
        self.__grid.Layout()

        
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
        melclass.deregister(self._name)


    def __recreateGrid(self):
        """Clears the :class:`.WidgetGrid`, and re-creates
        a :class:`.TextTagPanel` for every available melodic classification
        label.
        """

        grid   = self.__grid
        tagMap = self.__tagMap
        lut    = self.__lut
        
        grid.ClearGrid()
        tagMap.clear()

        grid.SetGridSize(len(lut), 2, growCols=[1])

        grid.SetColLabel(0, strings.labels[self, 'labelColumn'])
        grid.SetColLabel(1, strings.labels[self, 'componentColumn'])

        for i, label in enumerate(lut):
            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_NO_DUPLICATES |
                                               texttag.TTP_KEYBOARD_NAV))

            tags._label = label.name

            grid.SetText(  i, 0, label.name)
            grid.SetWidget(i, 1, tags)

            tagMap[label.internalName] = tags

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
        compStrs = [str(i) for i in range(1, numComps + 1)]

        for i, label in enumerate(lut):

            tags   = grid.GetWidget(i, 1)
            comps  = melclass.getComponents(label.internalName)
            
            colour = label.colour
            colour = [int(round(c  * 255.0)) for c in colour] 
            
            tags.ClearTags()

            tags.SetOptions(compStrs, [colour] * len(compStrs))

            for comp in comps:
                tags.AddTag(str(comp + 1))

                
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

        with melclass.skip(self._name):

            # If this component now has two labels, and
            # the other label is 'Unknown', remove the
            # 'Unknown' label.
            if len(melclass.getLabels(comp)) == 1 and \
               label != 'unknown'                 and \
               melclass.hasLabel(comp, 'unknown'):

                melclass.removeLabel(comp, 'unknown')
                self.__tagMap['unknown'].RemoveTag(str(comp + 1))

            melclass.addComponent(label, comp)

        # The WidgetGrid doesn't
        # resize itself when its
        # contents change size
        self.__grid.Layout()

    
    def __onTagRemoved(self, ev):
        """Called when a tag is removed from a :class:`.TextTagPanel`. Removes
        the corresponding label-component mapping from the
        :class:`.MelodicClassification` instance.
        """
        
        tags     = ev.GetEventObject()
        overlay  = self.__overlay
        lut      = self.__lut
        melclass = overlay.getICClassification()
        comp     = int(ev.tag) - 1
        label    = tags._label

        log.debug('Component removed from label {} ({})'.format(label, comp))

        with melclass.skip(self._name):
            
            melclass.removeComponent(label, comp)

            # If the component has no more labels,
            # give it an 'Unknown' label
            if len(melclass.getLabels(comp)) == 0:

                label = lut.getByName('unknown')
                
                melclass.addLabel(comp, label.name)
                
                tags   = self.__tagMap['unknown']
                colour = label.colour
                colour = [int(round(c  * 255.0)) for c in colour] 
                tags.AddTag(str(comp + 1), colour)

        # The WidgetGrid doesn't resize
        # itself when its contents change
        # size
        self.__grid.FitInside()


    def __onGridSelect(self, ev):
        """Called when a row is selected in the :class:`.WidgetGrid`. Makes
        sure that  the first tag in the :class:`.TextTagPanel` has the focus.
        """

        tags = self.__grid.GetWidget(ev.row, 1)

        log.debug('Grid row selected (label "{}")'.format(tags._label))
        
        tags.FocusNewTagCtrl()


    def __onTagSelect(self, ev):
        """Called when a tag from a :class:`.TextTagPanel` is selected.
        Changes the current :attr:`.NiftiOpts.volume` to the component
        corresponding to the selected tag.
        """

        comp        = int(ev.tag) - 1
        overlay     = self.__overlay
        opts        = self._displayCtx.getOpts(overlay)

        log.debug('Tag selected on label grid: component {}'.format(comp))
        
        opts.volume = comp
       

    def __lutChanged(self, lut, topic, value):
        """Called when the :class:`.LookupTable` changes. Re-creates and
        re-populates the :class:`.WidgetGrid`.
        """

        label, idx = value
        melclass   = self.__overlay.getICClassification()
        
        log.debug('Lookup table changed - re-creating label grid')

        # A label has been removed
        if topic == 'removed':

            # Only delete the corresponding
            # row if there are no components
            # with the deleted label.
            if len(melclass.getComponents(label.internalName)) == 0:
                self.__grid.DeleteRow(idx)
                self.__tagMap.pop(label.internalName)

        # A label has been added
        elif topic == 'added':
            self.__grid.InsertRow(idx)

            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_NO_DUPLICATES |
                                               texttag.TTP_KEYBOARD_NAV))

            tags._label = label.name

            self.__grid.SetText(  idx, 0, label.name)
            self.__grid.SetWidget(idx, 1, tags)
            self.__grid.Refresh()

            self.__tagMap[label.internalName] = tags

            tags.Bind(texttag.EVT_TTP_TAG_ADDED,   self.__onTagAdded)
            tags.Bind(texttag.EVT_TTP_TAG_REMOVED, self.__onTagRemoved)
            tags.Bind(texttag.EVT_TTP_TAG_SELECT,  self.__onTagSelect)

        # elif topic == 'label':
        self.__refreshTags()

        self.__grid.Layout()

        
    def __labelsChanged(self, melclass, topic, components):
        """Called when the :attr:`.MelodicClassification.labels` change.
        Re-populates the :class:`.WidgetGrid`.
        """
        log.debug('Melodic classification changed - '
                  'refreshing label grid tags')

        added = topic == 'added'

        for comp, label in components:
            tags = self.__tagMap.get(label, None)

            # Existing label
            if tags is not None:
                if added: tags.AddTag(   str(comp + 1))
                else:     tags.RemoveTag(str(comp + 1))

            # New label
            else:
                pass
