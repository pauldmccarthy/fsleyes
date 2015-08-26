#!/usr/bin/env python
#
# histogramcontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import                         props
import pwidgets.widgetlist  as widgetlist

import fsl.fsleyes.panel    as fslpanel
import fsl.fsleyes.tooltips as fsltooltips
import fsl.data.strings     as strings


class HistogramControlPanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, hsPanel):

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__hsPanel  = hsPanel
        self.__widgets  = widgetlist.WidgetList(self)
        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        histProps = ['histType',
                     'autoBin',
                     'showCurrent']
        plotProps = ['xLogScale',
                     'yLogScale',
                     'smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'autoScale']

        self.__widgets.AddGroup(
            'histSettings', strings.labels[self, 'histSettings'])

        for prop in histProps:
            if prop == 'histType':
                widget = props.makeWidget(
                    self.__widgets,
                    hsPanel,
                    prop,
                    labels=strings.choices['HistogramPanel.histType'])
            else:
                widget = props.makeWidget(self.__widgets, hsPanel, prop)
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[hsPanel, prop],
                tooltip=fsltooltips.properties[hsPanel, prop],
                groupName='histSettings')

        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[hsPanel, 'plotSettings'])
        
        for prop in plotProps:
            self.__widgets.AddWidget(
                props.makeWidget(self.__widgets, hsPanel, prop),
                tooltip=fsltooltips.properties[hsPanel, prop],
                displayName=strings.properties[hsPanel, prop],
                groupName='plotSettings')

        xlabel = props.makeWidget(self.__widgets, hsPanel, 'xlabel')
        ylabel = props.makeWidget(self.__widgets, hsPanel, 'ylabel')

        labels = wx.BoxSizer(wx.HORIZONTAL)

        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[hsPanel, 'xlabel']))
        labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[hsPanel, 'ylabel']))
        labels.Add(ylabel, flag=wx.EXPAND, proportion=1) 

        limits = props.makeListWidgets(self.__widgets, hsPanel, 'limits')
        xlims  = wx.BoxSizer(wx.HORIZONTAL)
        ylims  = wx.BoxSizer(wx.HORIZONTAL)
        
        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1) 

        self.__widgets.AddWidget(
            labels,
            displayName=strings.labels[hsPanel, 'labels'],
            tooltip=fsltooltips.misc[  hsPanel, 'labels'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            xlims,
            displayName=strings.labels[hsPanel, 'xlim'],
            tooltip=fsltooltips.misc[  hsPanel, 'xlim'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            ylims,
            displayName=strings.labels[hsPanel, 'ylim'],
            tooltip=fsltooltips.misc[  hsPanel, 'ylim'],
            groupName='plotSettings')

        # We store a ref to the currently selected
        # HistogramSeries instance, and to the
        # HistogramSeries.nbins widget, so we can
        # enable/disable it
        self.__currentHs = None
        self.__nbins     = None
        
        hsPanel.addListener('selectedSeries',
                            self._name,
                            self.__selectedSeriesChanged)
        
        hsPanel.addListener('dataSeries',
                            self._name,
                            self.__selectedSeriesChanged)
        hsPanel.addListener('autoBin',
                            self._name,
                            self.__autoBinChanged) 

        self.__selectedSeriesChanged()


    def destroy(self):
        self.__hsPanel.removeListener('selectedSeries', self._name)
        self.__hsPanel.removeListener('dataSeries',     self._name)
        if self.__currentHs is not None:
            self.__currentHs.removeListener('label', self._name)

        fslpanel.FSLEyesPanel.destroy(self)

        
    def __selectedSeriesChanged(self, *a):

        panel = self.__hsPanel 
        
        if len(panel.dataSeries) == 0:
            self.__currentHs = None

        else:
            self.__currentHs = panel.dataSeries[panel.selectedSeries]

        self.__updateCurrentProperties()


    def __hsLabelChanged(self, *a):
        if self.__currentHs is None:
            return
        
        self.__widgets.RenameGroup(
            'currentSettings',
            strings.labels[self, 'currentSettings'].format(
                self.__currentHs.label)) 


    def __updateCurrentProperties(self):

        expanded  = False
        scrollPos = self.__widgets.GetViewStart()
        
        if self.__widgets.HasGroup('currentSettings'):
            expanded = self.__widgets.IsExpanded('currentSettings')
            self.__widgets.RemoveGroup('currentSettings')
            self.__nbins = None

        if self.__currentHs is None:
            return
        else:
            self.__currentHs.removeListener('label', self._name)

        self.__widgets.AddGroup(
            'currentSettings',
            strings.labels[self.__hsPanel, 'currentSettings'].format(
                self.__currentHs.label))

        wlist = self.__widgets
        hs    = self.__currentHs

        hs.addListener('label', self._name, self.__hsLabelChanged)

        self.__nbins = props.makeWidget(wlist, hs, 'nbins', showLimits=False)
        
        volume    = props.makeWidget(wlist, hs, 'volume',    showLimits=False)
        dataRange = props.makeWidget(
            wlist,
            hs,
            'dataRange',
            showLimits=False,
            labels=[strings.choices['HistogramPanel.dataRange.min'],
                    strings.choices['HistogramPanel.dataRange.max']])
        
        ignoreZeros     = props.makeWidget(wlist, hs, 'ignoreZeros')
        showOverlay     = props.makeWidget(wlist, hs, 'showOverlay')
        includeOutliers = props.makeWidget(wlist, hs, 'includeOutliers')

        wlist.AddWidget(ignoreZeros,
                        groupName='currentSettings',
                        displayName=strings.properties[hs, 'ignoreZeros'],
                        tooltip=fsltooltips.properties[hs, 'ignoreZeros'])
        wlist.AddWidget(showOverlay,
                        groupName='currentSettings',
                        displayName=strings.properties[hs, 'showOverlay'],
                        tooltip=fsltooltips.properties[hs, 'showOverlay'])
        wlist.AddWidget(includeOutliers,
                        groupName='currentSettings',
                        displayName=strings.properties[hs, 'includeOutliers'],
                        tooltip=fsltooltips.properties[hs, 'includeOutliers']) 
        wlist.AddWidget(self.__nbins,
                        groupName='currentSettings',
                        displayName=strings.properties[hs, 'nbins'],
                        tooltip=fsltooltips.properties[hs, 'nbins'])
        wlist.AddWidget(volume,
                        groupName='currentSettings',
                        displayName=strings.properties[hs, 'volume'],
                        tooltip=fsltooltips.properties[hs, 'volume'])
        wlist.AddWidget(dataRange,
                        groupName='currentSettings',
                        displayName=strings.properties[hs, 'dataRange'],
                        tooltip=fsltooltips.properties[hs, 'dataRange'])

        if expanded:
            wlist.Expand('currentSettings')

        self.__widgets.Scroll(scrollPos)

        volume      .Enable(hs.overlay.is4DImage())
        self.__nbins.Enable(not self.__hsPanel.autoBin)
        

    def __autoBinChanged(self, *a):

        if self.__currentHs is None or self.__nbins is None:
            return
        self.__nbins.Enable(not self.__hsPanel.autoBin)
