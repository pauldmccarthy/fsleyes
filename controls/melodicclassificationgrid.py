#!/usr/bin/env python
#
# melodicclassificationgrid.py - the ComponentGrid and LabelGrid classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx

import pwidgets.widgetgrid        as widgetgrid
import pwidgets.texttag           as texttag

import fsl.fsleyes.panel          as fslpanel
import fsl.fsleyes.colourmaps     as fslcm
import fsl.fsleyes.displaycontext as fsldisplay
import fsl.data.melodicimage      as fslmelimage
import fsl.data.strings           as strings


class ComponentGrid(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, lut):
        
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

        lut        .addListener('labels', self._name, self.__lutChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__overlay = None
        self.__selectedOverlayChanged()

        
    def destroy(self):
        """
        """
        
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__lut       .removeListener('labels',          self._name)
        self.__deregisterCurrentOverlay()
        
        self.__lut = None

        fslpanel.FSLEyesPanel.destroy(self)


    def __deregisterCurrentOverlay(self):
        """
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

        
    def __selectedOverlayChanged(self, *a):
        """
        """

        self.__deregisterCurrentOverlay()
        self.__grid.ClearGrid()

        overlay = self._displayCtx.getSelectedOverlay()

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
                             self.__selectedOverlayChanged)
        
        self.__recreateTags()
        self.__volumeChanged()

        
    def __recreateTags(self):
        """
        """

        overlay  = self.__overlay
        numComps = overlay.numComponents()

        for i in range(numComps):

            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_ALLOW_NEW_TAGS |
                                               texttag.TTP_ADD_NEW_TAGS   |
                                               texttag.TTP_NO_DUPLICATES  |
                                               texttag.TTP_KEYBOARD_NAV))

            # Store the component number on the tag
            # panel, so we know which component we
            # are dealing with in the __onTagAdded
            # and __onTagRemoved methods.
            tags._melodicComponent = i

            self.__grid.SetText(  i, 0, str(i))
            self.__grid.SetWidget(i, 1, tags)

            tags.Bind(texttag.EVT_TTP_TAG_ADDED_EVENT,   self.__onTagAdded)
            tags.Bind(texttag.EVT_TTP_TAG_REMOVED_EVENT, self.__onTagRemoved)

        self.__refreshTags()

        self.Layout()

        
    def __refreshTags(self):
        
        overlay  = self.__overlay
        melclass = overlay.getICClassification()
        numComps = overlay.numComponents() 
        lut      = self.__lut

        labels  = [l.name()   for l in lut.labels]
        colours = [l.colour() for l in lut.labels]

        # Compile lists of all the existing
        # labels, and the colours for each one
        for i in range(numComps):

            for label in melclass.getLabels(i):
                if label in labels:
                    continue
                
                colour = self.__addNewLutLabel(label).colour()
                
                labels .append(label)
                colours.append(colour)
        
        for i in range(len(colours)):
            colours[i] = [int(round(c * 255)) for c in colours[i]] 

        for row in range(numComps):
            tags = self.__grid.GetWidget(row, 1)

            tags.ClearTags()
            tags.SetOptions(labels, colours)

            for label in melclass.getLabels(row):
                tags.AddTag(label)


    def __addNewLutLabel(self, label, colour=None):
        """
        """
        
        lut   = self.__lut
        value = lut.max() + 1

        if colour is None:
            colour = fslcm.randomBrightColour()

        lut.disableListener('labels', self._name)
        lut.set(value, name=label, colour=colour)
        lut.enableListener('labels', self._name)

        self.__refreshTags()

        return lut.get(value)
                

    def __onTagAdded(self, ev):
        """
        """

        tags      = ev.GetEventObject()
        label     = ev.tag
        component = tags._melodicComponent
        overlay   = self.__overlay
        lut       = self.__lut 
        melclass  = overlay.getICClassification()

        # Add the new label to the melodic component
        melclass.disableListener('labels', self._name)
        melclass.addLabel(component, label)

        # If the tag panel previously just contained
        # the 'Unknown' tag, remove that tag
        if tags.TagCount() == 2 and tags.HasTag('Unknown'):
            melclass.removeLabel(component, 'Unknown')
            tags.RemoveTag('Unknown')

        melclass.enableListener('labels', self._name)

        # If the newly added tag is not in
        # the lookup table, add it in
        if lut.getByName(label) is None:
            colour = tags.GetTagColour(label)
            colour = [c / 255.0 for c in colour]
            self.__addNewLutLabel(label, colour)

        self.__grid.FitInside()

        
    def __onTagRemoved(self, ev):
        """
        """
        
        tags      = ev.GetEventObject()
        label     = ev.tag
        component = tags._melodicComponent
        overlay   = self.__overlay
        melclass  = overlay.getICClassification()

        # Remove the label from
        # the melodic component
        melclass.disableListener('labels', self._name)
        melclass.removeLabel(component, label)
        melclass.enableListener('labels', self._name)
 
        # If the tag panel now has no tags,
        # add the 'Unknown' tag back in.
        if tags.TagCount() == 0:
            tags.AddTag('Unknown') 

        self.__grid.FitInside()


    def __onGridSelect(self, ev):

        component   = ev.row
        opts        = self._displayCtx.getOpts(self.__overlay)

        opts.disableListener('volume', self._name)
        opts.volume = component
        opts.enableListener('volume', self._name)

        tags = self.__grid.GetWidget(ev.row, 1)

        tags.FocusNewTagCtrl()


    def __volumeChanged(self, *a):
        
        opts = self._displayCtx.getOpts(self.__overlay)
        self.__grid.SetSelection(opts.volume, -1)

        tags = self.__grid.GetWidget(opts.volume, 1)
        tags.FocusNewTagCtrl()


    def __labelsChanged(self, *a):
        self.__refreshTags()


    def __lutChanged(self, *a):
        self.__refreshTags()




class LabelGrid(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, lut):
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__grid  = widgetgrid.WidgetGrid(self)
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer) 
