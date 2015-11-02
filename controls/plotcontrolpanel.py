#!/usr/bin/env python
#
# plotcontrolpanel.py - The PlotControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import wx

import props

import pwidgets.widgetlist        as widgetlist

import fsl.fsleyes.panel          as fslpanel
import fsl.fsleyes.tooltips       as fsltooltips
import fsl.fsleyes.displaycontext as fsldisplay
import fsl.data.strings           as strings


class PlotControlPanel(fslpanel.FSLEyesPanel):


    def __init__(self, parent, overlayList, displayCtx, plotPanel):
        """Create a ``PlotControlPanel``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg plotPanel:   The :class:`.PlotPanel` associated with this
                          ``PlotControlPanel``.
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)
        
        self.__plotPanel = plotPanel
        self.__widgets   = widgetlist.WidgetList(self)
        self.__sizer     = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        self.__widgets.AddGroup(
            'customPlotSettings',
            strings.labels[self, 'customPlotSettings'])

        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[self, 'plotSettings']) 

        self.generateCustomPlotPanelWidgets('customPlotSettings')
        self.generatePlotPanelWidgets(      'plotSettings')

        # Delete the custom group if
        # nothing has been added to it
        if self.__widgets.GroupSize('customPlotSettings') == 0:
            self.__widgets.RemoveGroup('customPlotSettings') 

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)

        # This attribute keeps track of the currently
        # selected overlay, so the widget list group
        # names can be updated if the overlay name
        # changes.
        self.__selectedOverlay = None
        self.__selectedOverlayChanged()

        
    def destroy(self):
        """Must be called when this ``PlotControlPanel`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.FSLEyesPanel.destroy` method.
        """
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__selectedOverlay is not None:
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self._name)
            
        fslpanel.FSLEyesPanel.destroy(self)


    def getPlotPanel(self):
        return self.__plotPanel

    
    def getWidgetList(self):
        return self.__widgets

    
    def generateCustomPlotPanelWidgets(self, groupName):
        pass


    def generatePlotPanelWidgets(self, groupName):
        """Adds a collection of widgets to the given :class:`.WidgetList`,
        allowing the properties of the given :class:`.PlotPanel` instance
        to be changed.
        """

        widgetList = self.__widgets
        plotPanel  = self.__plotPanel

        plotProps = ['xLogScale',
                     'yLogScale',
                     'smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'autoScale']

        for prop in plotProps:
            widgetList.AddWidget(
                props.makeWidget(widgetList, plotPanel, prop),
                displayName=strings.properties[plotPanel, prop],
                tooltip=fsltooltips.properties[plotPanel, prop],
                groupName=groupName)

        xlabel = props.makeWidget(widgetList, plotPanel, 'xlabel')
        ylabel = props.makeWidget(widgetList, plotPanel, 'ylabel')

        labels = wx.BoxSizer(wx.HORIZONTAL)

        labels.Add(wx.StaticText(widgetList,
                                 label=strings.labels[self, 'xlabel']))
        labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
        labels.Add(wx.StaticText(widgetList,
                                 label=strings.labels[self, 'ylabel']))
        labels.Add(ylabel, flag=wx.EXPAND, proportion=1) 

        limits = props.makeListWidgets(widgetList, plotPanel, 'limits')
        xlims  = wx.BoxSizer(wx.HORIZONTAL)
        ylims  = wx.BoxSizer(wx.HORIZONTAL)

        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1) 

        widgetList.AddWidget(
            labels,
            displayName=strings.labels[self, 'labels'],
            tooltip=fsltooltips.misc[  self, 'labels'],
            groupName=groupName)
        widgetList.AddWidget(
            xlims,
            displayName=strings.labels[self, 'xlim'],
            tooltip=fsltooltips.misc[  self, 'xlim'],
            groupName=groupName)
        widgetList.AddWidget(
            ylims,
            displayName=strings.labels[self, 'ylim'],
            tooltip=fsltooltips.misc[  self, 'ylim'],
            groupName=groupName)



    def refreshDataSeriesWidgets(self):
        if self.__selectedOverlay is not None:
            try:
                display = self._displayCtx.getDisplay(self.__selectedOverlay)
                display.removeListener('name', self._name)
                
            # The overlay may have been
            # removed from the overlay list
            except fsldisplay.InvalidOverlayError:
                pass
                
            self.__selectedOverlay = None

        if self.__widgets.HasGroup('currentDSSettings'):
            self.__widgets.RemoveGroup('currentDSSettings')
        if self.__widgets.HasGroup('customDSSettings'):
            self.__widgets.RemoveGroup('customDSSettings') 

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ds = self.__plotPanel.getDataSeries(overlay)

        if ds is None:
            return

        self.__selectedOverlay = overlay

        display = self._displayCtx.getDisplay(overlay)

        display.addListener('name',
                            self._name,
                            self.__selectedOverlayNameChanged)

        self.__widgets.AddGroup(
            'currentDSSettings',
            strings.labels[self, 'currentDSSettings'].format(display.name))
        self.__widgets.AddGroup(
            'customDSSettings',
            strings.labels[self, 'customDSSettings'].format(display.name)) 
        
        self.generateDataSeriesWidgets(      ds, 'currentDSSettings')
        self.generateCustomDataSeriesWidgets(ds, 'customDSSettings')

        # Delete the custom group if
        # nothing has been added to it
        if self.__widgets.GroupSize('customDSSettings') == 0:
            self.__widgets.RemoveGroup('customDSSettings') 
 
    
    def generateDataSeriesWidgets(self, ds, groupName):
        """Adds a collection of widgets to the given :class:`.WidgetList`,
        allowing the properties of the given :class:`.DataSeries` instance
        to be changed.

        :arg ds:         The :class:`.DataSeries` instance. 
        """
        
        widgetList = self.__widgets
        
        colour    = props.makeWidget(widgetList, ds, 'colour')
        alpha     = props.makeWidget(widgetList, ds, 'alpha',
                                     showLimits=False, spin=False)
        lineWidth = props.makeWidget(widgetList, ds, 'lineWidth')
        lineStyle = props.makeWidget(
            widgetList,
            ds,
            'lineStyle',
            labels=strings.choices[ds, 'lineStyle'])

        widgetList.AddWidget(
            colour,
            displayName=strings.properties[ds, 'colour'],
            tooltip=fsltooltips.properties[ds, 'colour'],
            groupName=groupName)
        widgetList.AddWidget(
            alpha,
            displayName=strings.properties[ds, 'alpha'],
            tooltip=fsltooltips.properties[ds, 'alpha'],
            groupName=groupName)
        widgetList.AddWidget(
            lineWidth,
            displayName=strings.properties[ds, 'lineWidth'],
            tooltip=fsltooltips.properties[ds, 'lineWidth'],
            groupName=groupName) 
        widgetList.AddWidget(
            lineStyle,
            displayName=strings.properties[ds, 'lineStyle'],
            tooltip=fsltooltips.properties[ds, 'lineStyle'],
            groupName=groupName)


    def generateCustomDataSeriesWidgets(self, ds, groupName):
        """
        """
        pass
            

    def __selectedOverlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` property for the currently
        selected overlay changes. Updates the display name of the *FEAT plot
        settings* and *current time course* sections if necessary.
        """
        display = self._displayCtx.getDisplay(self.__selectedOverlay)
        
        if self.__widgets.HasGroup('currentDSSettings'):
            self.__widgets.RenameGroup(
                'currentDSSettings',
                strings.labels[self, 'currentDSettings'].format(display.name))
        
        if self.__widgets.HasGroup('customDSSettings'):
            self.__widgets.RenameGroup(
                'customDSSettings',
                strings.labels[self, 'customDSettings'].format(display.name)) 

    
    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes. 
        """
        self.refreshDataSeriesWidgets()
