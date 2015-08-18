#!/usr/bin/env python
#
# atlasoverlaypanel.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import logging

import wx

import pwidgets.elistbox as elistbox

import fsl.data.atlases  as atlases
import fsl.data.strings  as strings
import fsl.utils.dialog  as dialog
import fsl.fsleyes.panel as fslpanel


log = logging.getLogger(__name__)


class OverlayListWidget(wx.Panel):

    def __init__(self, parent, atlasID, atlasPanel, labelIdx=None):

        wx.Panel.__init__(self, parent)
        
        self.atlasID    = atlasID
        self.atlasDesc  = atlases.getAtlasDescription(atlasID)
        self.atlasPanel = atlasPanel
        self.labelIdx   = labelIdx

        self.enableBox = wx.CheckBox(self)
        self.enableBox.SetValue(False)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.enableBox, flag=wx.EXPAND)

        self.enableBox.Bind(wx.EVT_CHECKBOX, self._onEnable)
        
        if labelIdx is not None:
            self.locateButton = wx.Button(self,
                                          label='+',
                                          style=wx.BU_EXACTFIT)
            self.sizer.Add(self.locateButton, flag=wx.EXPAND)

            self.locateButton.Bind(wx.EVT_BUTTON, self._onLocate)
        
    def _onEnable(self, ev):
        self.atlasPanel.toggleOverlay(
            self.atlasID,
            self.labelIdx,
            self.atlasDesc.atlasType == 'label')

    def _onLocate(self, ev):
        self.atlasPanel.locateRegion(self.atlasID, self.labelIdx)

        

class AtlasOverlayPanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, atlasPanel):

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__enabledOverlays = {}
        self.__atlasPanel      = atlasPanel
        self.__contentPanel    = wx.SplitterWindow(self,
                                                   style=wx.SP_LIVE_UPDATE)
        self.__atlasList       = elistbox.EditableListBox(
            self.__contentPanel,
            style=(elistbox.ELB_NO_ADD    |
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        self.__regionPanel     = wx.Panel(   self.__contentPanel)
        self.__regionFilter    = wx.TextCtrl(self.__regionPanel)

        atlasDescs = atlases.listAtlases()

        self.__regionLists = [None] * len(atlasDescs)

        self.__contentPanel.SetMinimumPaneSize(50)
        self.__contentPanel.SplitVertically(self.__atlasList,
                                            self.__regionPanel)
        self.__contentPanel.SetSashGravity(0.5) 
        
        self.__sizer       = wx.BoxSizer(wx.HORIZONTAL)
        self.__regionSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.__regionSizer.Add(self.__regionFilter, flag=wx.EXPAND)
        self.__regionSizer.AddStretchSpacer()        
        
        self.__sizer      .Add(self.__contentPanel,
                               flag=wx.EXPAND,
                               proportion=1)
        
        self.__regionPanel.SetSizer(self.__regionSizer) 
        self              .SetSizer(self.__sizer)

        for i, atlasDesc in enumerate(atlasDescs):
            self.__atlasList.Append(atlasDesc.name, atlasDesc)
            self.__updateAtlasState(i)
            widget = OverlayListWidget(self.__atlasList,
                                       atlasDesc.atlasID,
                                       atlasPanel)
            self.__atlasList.SetItemWidget(i, widget)
        
        self.__regionFilter.Bind(wx.EVT_TEXT, self.__onRegionFilter)
        self.__atlasList.Bind(elistbox.EVT_ELB_SELECT_EVENT,
                              self.__onAtlasSelect)

        self.__regionSizer.Layout()
        self.__sizer      .Layout()

        self.SetMinSize(self.__sizer.GetMinSize())


    def setOverlayState(self, atlasID, labelIdx, summary, state):

        atlasDesc = atlases.getAtlasDescription(atlasID)
        log.debug('Setting {}/{} overlay state to {}'.format(
            atlasID, labelIdx, state))

        if labelIdx is None:
            widget = self.__atlasList.GetItemWidget(atlasDesc.index)
            widget.enableBox.SetValue(state)
        else:
            regionList = self.__regionLists[atlasDesc.index]
            
            if regionList is not None:
                regionList.GetItemWidget(labelIdx).enableBox.SetValue(state)


    def __onRegionFilter(self, ev):
        
        filterStr = self.__regionFilter.GetValue().lower().strip()

        for i, listBox in enumerate(self.__regionLists):

            self.__updateAtlasState(i)

            if listBox is not None:
                listBox.ApplyFilter(filterStr, ignoreCase=True)


    def __updateAtlasState(self, atlasIdx):

        filterStr = self.__regionFilter.GetValue().lower().strip()
        atlasDesc = self.__atlasList.GetItemData(atlasIdx)

        if filterStr == '':
            nhits = 0
        else:
            nhits = len(filter(
                lambda l: filterStr in l.name.lower(),
                atlasDesc.labels))

        if nhits == 0:
            weight = wx.FONTWEIGHT_LIGHT
            colour = '#404040'
        else:
            weight = wx.FONTWEIGHT_BOLD
            colour = '#000000'

        font = self.__atlasList.GetItemFont(atlasIdx)
        font.SetWeight(weight)
        
        self.__atlasList.SetItemFont(atlasIdx, font)
        self.__atlasList.SetItemForegroundColour(atlasIdx, colour, colour) 
 
            
    def __onAtlasSelect(self, ev):

        atlasDesc  = ev.data
        atlasIdx   = ev.idx
        regionList = self.__regionLists[atlasIdx]

        if regionList is None:
            
            regionList = elistbox.EditableListBox(
                self.__regionPanel,
                style=(elistbox.ELB_NO_ADD    |
                       elistbox.ELB_NO_REMOVE |
                       elistbox.ELB_NO_MOVE))


            def buildRegionList():

                log.debug('Creating region list for {} ({})'.format(
                    atlasDesc.atlasID, id(regionList)))

                self.__regionLists[atlasIdx] = regionList

                for i, label in enumerate(atlasDesc.labels):
                    regionList.Append(label.name)
                    widget = OverlayListWidget(regionList,
                                               atlasDesc.atlasID,
                                               self.__atlasPanel,
                                               label.index)
                    regionList.SetItemWidget(i, widget)
                    wx.Yield()

                filterStr = self.__regionFilter.GetValue().lower().strip()
                regionList.ApplyFilter(filterStr, ignoreCase=True)

                self.__updateAtlasState(atlasIdx)

            dialog.ProcessingDialog(
                None,
                strings.messages[self, 'loadRegions'].format(atlasDesc.name),
                buildRegionList).Run(mainThread=True)
            
        log.debug('Showing region list for {} ({})'.format(
            atlasDesc.atlasID, id(regionList)))

        old = self.__regionSizer.GetItem(1).GetWindow()
        
        if old is not None:
            old.Show(False)
            
        regionList.Show(True)
        self.__regionSizer.Remove(1)
        
        self.__regionSizer.Insert(1, regionList, flag=wx.EXPAND, proportion=1)
        self.__regionSizer.Layout()
