#!/usr/bin/env python
#
# histogramlistpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx

import pwidgets.elistbox      as elistbox
import fsl.fsleyes.panel      as fslpanel
import fsl.fsleyes.colourmaps as fslcm

import                           timeserieslistpanel 
    

class HistogramListPanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, histPanel):

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__hsPanel      = histPanel
        self.__hsList       = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__hsList, flag=wx.EXPAND, proportion=1)

        self.__hsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__hsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__hsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__hsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        self.__hsPanel.addListener('dataSeries',
                                   self._name,
                                   self.__histSeriesChanged)

        self.__histSeriesChanged()
        self.Layout()

        
    def destroy(self):
        self.__hsPanel.removeListener('dataSeries', self._name)
        fslpanel.FSLEyesPanel.destroy(self)


    def getListBox(self):
        return self.__hsList


    def __histSeriesChanged(self, *a):

        self.__hsList.Clear()

        for hs in self.__hsPanel.dataSeries:
            widg = timeserieslistpanel.TimeSeriesWidget(self, hs)
            
            self.__hsList.Append(hs.label,
                                 clientData=hs,
                                 extraWidget=widg)

        if len(self.__hsPanel.dataSeries) > 0:
            self.__hsList.SetSelection(0)
        
    
    def __onListAdd(self, ev):
        hs = self.__hsPanel.getCurrent()

        if hs is None:
            return
        
        hs.alpha     = 1
        hs.lineWidth = 2
        hs.lineStyle = '-'
        hs.colour    = fslcm.randomColour()
        hs.label     = hs.overlay.name

        self.__hsPanel.dataSeries.append(hs)
        self.__hsPanel.selectedSeries = self.__hsList.GetSelection()

        
    def __onListEdit(self, ev):
        ev.data.label = ev.label

        
    def __onListSelect(self, ev):
        overlay = ev.data.overlay
        self._displayCtx.selectedOverlay = self._overlayList.index(overlay)
        self.__hsPanel.selectedSeries = ev.idx

        
    def __onListRemove(self, ev):
        self.__hsPanel.dataSeries.remove(ev.data)
        self.__hsPanel.selectedSeries = self.__hsList.GetSelection()
        ev.data.destroy()
