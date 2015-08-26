#!/usr/bin/env python
#
# timeserieslistpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import          copy

import          wx
import numpy as np

import                           props
import pwidgets.elistbox      as elistbox
import fsl.fsleyes.panel      as fslpanel
import fsl.fsleyes.tooltips   as fsltooltips
import fsl.data.strings       as strings
import fsl.fsleyes.colourmaps as fslcm


class TimeSeriesWidget(wx.Panel):

    def __init__(self, parent, timeSeries):

        wx.Panel.__init__(self, parent)

        self.colour    = props.makeWidget(self,
                                          timeSeries,
                                          'colour')
        self.alpha     = props.makeWidget(self,
                                          timeSeries,
                                          'alpha',
                                          slider=True,
                                          spin=False,
                                          showLimits=False) 
        self.lineWidth = props.makeWidget(self,
                                          timeSeries,
                                          'lineWidth')
        self.lineStyle = props.makeWidget(
            self,
            timeSeries,
            'lineStyle',
            labels=strings.choices['DataSeries.lineStyle'])

        self.colour.SetToolTipString(
            fsltooltips.properties[timeSeries, 'colour'])
        self.alpha.SetToolTipString(
            fsltooltips.properties[timeSeries, 'alpha'])
        self.lineWidth.SetToolTipString(
            fsltooltips.properties[timeSeries, 'lineWidth'])
        self.lineStyle.SetToolTipString(
            fsltooltips.properties[timeSeries, 'lineStyle'])

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.colour)
        self.sizer.Add(self.alpha)
        self.sizer.Add(self.lineWidth)
        self.sizer.Add(self.lineStyle)

        self.Layout()
    

class TimeSeriesListPanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, timeSeriesPanel):

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel      = timeSeriesPanel
        self.__currentLabel = wx.StaticText(self)
        self.__tsList       = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__currentLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__tsList,       flag=wx.EXPAND, proportion=1)

        self.__tsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__tsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__tsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__tsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        displayCtx    .addListener('selectedOverlay',
                                   self._name,
                                   self.__locationChanged)
        displayCtx    .addListener('location',
                                   self._name,
                                   self.__locationChanged) 
        overlayList   .addListener('overlays',
                                   self._name,
                                   self.__locationChanged)
        self.__tsPanel.addListener('dataSeries',
                                   self._name,
                                   self.__timeSeriesChanged)

        self.__timeSeriesChanged()
        self.__locationChanged()
        self.Layout()

        
    def destroy(self):
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__tsPanel   .removeListener('dataSeries',      self._name)
        
        fslpanel.FSLEyesPanel.destroy(self)


    def __makeLabel(self, ts):

        display = self._displayCtx.getDisplay(ts.overlay)

        return '{} [{} {} {}]'.format(display.name,
                                      ts.coords[0],
                                      ts.coords[1],
                                      ts.coords[2])


    def __makeFEATModelTSLabel(self, parentTs, modelTs):

        import fsl.fsleyes.views.timeseriespanel as tsp

        overlay = modelTs.overlay
        display = self._displayCtx.getDisplay(overlay)

        if isinstance(modelTs, tsp.FEATResidualTimeSeries):
            return '{} ({})'.format(
                parentTs.label,
                strings.labels[modelTs])
        
        elif isinstance(modelTs, tsp.FEATEVTimeSeries):
            return '{} EV{} ({})'.format(
                display.name, 
                modelTs.idx + 1,
                overlay.evNames()[modelTs.idx])

        label = '{} ({})'.format(
            parentTs.label,
            strings.labels[modelTs, modelTs.fitType])

        if modelTs.fitType == 'full':
            return label
        
        elif modelTs.fitType == 'cope':
            return label.format(
                modelTs.idx + 1,
                overlay.contrastNames()[modelTs.idx])
        
        elif modelTs.fitType == 'pe':
            return label.format(modelTs.idx + 1) 


    def __timeSeriesChanged(self, *a):

        self.__tsList.Clear()

        for ts in self.__tsPanel.dataSeries:
            widg = TimeSeriesWidget(self, ts)
            self.__tsList.Append(
                ts.label,
                clientData=ts,
                tooltip=fsltooltips.properties[ts, 'label'],
                extraWidget=widg)


    def __locationChanged(self, *a):

        ts = self.__tsPanel.getCurrent()

        if ts is None:
            self.__currentLabel.SetLabel('')
            return
        
        self.__currentLabel.SetLabel(self.__makeLabel(ts))

    
    def __onListAdd(self, ev):
        
        import fsl.fsleyes.views.timeseriespanel as tsp
        
        ts = self.__tsPanel.getCurrent()

        if ts is None:
            return

        ts           = copy.copy(ts)

        ts.alpha     = 1
        ts.lineWidth = 2
        ts.lineStyle = '-'
        ts.colour    = fslcm.randomColour()
        ts.label     = self.__makeLabel(ts)

        self.__tsPanel.dataSeries.append(ts)

        if isinstance(ts, tsp.FEATTimeSeries):
            
            modelTs = ts.getModelTimeSeries()
            modelTs.remove(ts)

            for mts in modelTs:

                mts.alpha     = 1
                mts.lineWidth = 2
                mts.lineStyle = '-'
                mts.label     = self.__makeFEATModelTSLabel(ts, mts)

            self.__tsPanel.dataSeries.extend(modelTs)

        
    def __onListEdit(self, ev):
        ev.data.label = ev.label

        
    def __onListSelect(self, ev):

        overlay = ev.data.overlay
        coords  = ev.data.coords
        opts    = self._displayCtx.getOpts(overlay)
        vox     = np.array(coords)
        disp    = opts.transformCoords([vox], 'voxel', 'display')[0]

        self._displayCtx.selectedOverlay = self._overlayList.index(overlay)
        self._displayCtx.location        = disp

        
    def __onListRemove(self, ev):
        self.__tsPanel.dataSeries.remove(ev.data)
