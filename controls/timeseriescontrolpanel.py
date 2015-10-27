#!/usr/bin/env python
#
# timeseriescontrolpanel.py - The TimeSeriesControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesControlPanel` a *FSLeyes
control* which allows the user to configure a :class:`.TimeSeriesPanel`.
"""


import wx

import                                    props
import pwidgets.widgetlist             as widgetlist

import fsl.fsleyes.panel               as fslpanel
import fsl.fsleyes.plotting.timeseries as timeseries
import fsl.fsleyes.tooltips            as fsltooltips
import fsl.data.strings                as strings


class TimeSeriesControlPanel(fslpanel.FSLEyesPanel):
    """The ``TimeSeriesControlPanel`` is a :class:`.FSLEyesPanel` which allows
    the user to configure a :class:`.TimeSeriesPanel`. It contains controls
    which are linked to the properties of the :class:`.TImeSeriesPanel`,
    (which include properties defined on the :class:`.PlotPanel` base class),
    and the :class:`.TimeSeries` class.

    
    A ``TimeSeriesControlPanel`` looks something like this:

    .. image:: images/timeseriescontrolpanel.png
       :scale: 50%
       :align: center


    The settings shown on a ``TimeSeriesControlPanel`` are organised into three
    or four sections:

     - The *Time series plot settings* section has controls which are linked to
       properties of the :class:`.TimeSeriesPanel` class.
    
     - The *General plot settings* section has controls which are linked to
       properties of the :class:`.PlotPanel` base class.
    
     - The *Settings for the current time course* section has controls which
       are linked to properties of the :class:`.TimeSeries` class. These
       properties define how the *current* time course is displayed (see the
       :class:`.TimeSeriesPanel` class documentation).
    
     - The *FEAT plot settings* is only shown if the currently selected overlay
       is a :class:`.FEATImage`. It has controls which are linked to properties
       of the :class:`.FEATTimeSeries` class.
    """

    
    def __init__(self, parent, overlayList, displayCtx, tsPanel):
        """Create a ``TimeSeriesControlPanel``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg tsPanel:     The :class:`.TimeSeriesPanel` associated with this
                          ``TimeSeriesControlPanel``.
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel = tsPanel
        self.__widgets = widgetlist.WidgetList(self)
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        tsProps   = ['plotMode',
                     'usePixdim',
                     'showCurrent',
                     'showAllCurrent']
        plotProps = ['xLogScale',
                     'yLogScale',
                     'smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'autoScale']

        self.__widgets.AddGroup(
            'tsSettings',
            strings.labels[self, 'tsSettings'])

        for prop in tsProps:
            if prop == 'plotMode': 
                widget = props.makeWidget(
                    self.__widgets,
                    tsPanel,
                    prop,
                    labels=strings.choices['TimeSeriesPanel.plotMode'])
            else:
                widget = props.makeWidget(self.__widgets, tsPanel, prop)
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[tsPanel, prop],
                tooltip=fsltooltips.properties[tsPanel, prop],
                groupName='tsSettings')

        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[tsPanel, 'plotSettings'])
        
        for prop in plotProps:
            self.__widgets.AddWidget(
                props.makeWidget(self.__widgets, tsPanel, prop),
                displayName=strings.properties[tsPanel, prop],
                tooltip=fsltooltips.properties[tsPanel, prop],
                groupName='plotSettings')

        xlabel = props.makeWidget(self.__widgets, tsPanel, 'xlabel')
        ylabel = props.makeWidget(self.__widgets, tsPanel, 'ylabel')

        labels = wx.BoxSizer(wx.HORIZONTAL)

        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[tsPanel, 'xlabel']))
        labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[tsPanel, 'ylabel']))
        labels.Add(ylabel, flag=wx.EXPAND, proportion=1) 

        limits = props.makeListWidgets(self.__widgets, tsPanel, 'limits')
        xlims  = wx.BoxSizer(wx.HORIZONTAL)
        ylims  = wx.BoxSizer(wx.HORIZONTAL)
        
        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1) 

        self.__widgets.AddWidget(
            labels,
            displayName=strings.labels[tsPanel, 'labels'],
            tooltip=fsltooltips.misc[  tsPanel, 'labels'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            xlims,
            displayName=strings.labels[tsPanel, 'xlim'],
            tooltip=fsltooltips.misc[  tsPanel, 'xlim'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            ylims,
            displayName=strings.labels[tsPanel, 'ylim'],
            tooltip=fsltooltips.misc[  tsPanel, 'ylim'],
            groupName='plotSettings')

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)

        tsPanel.addListener('showCurrent',
                            self._name,
                            self.__showCurrentChanged)

        self.__showCurrentChanged()

        # This attribute keeps track of the currently
        # selected overlay, but only if said overlay
        # is a FEATImage.
        self.__selectedOverlay = None
        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``TimeSeriesControlPanel`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.FSLEyesPanel.destroy` method.
        """
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__selectedOverlay is not None:
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self._name)
            
        fslpanel.FSLEyesPanel.destroy(self)


    def __showCurrentChanged(self, *a):
        """Called when the :attr:`.TimeSeriesPanel.showCurrent` property
        changes. Shows hides the  *Settings for the current time course*
        section.
        """
        widgets     = self.__widgets
        tsPanel     = self.__tsPanel
        showCurrent = tsPanel.showCurrent
        areShown    = widgets.HasGroup('currentSettings')

        if (not showCurrent) and areShown:
            widgets.RemoveGroup('currentSettings')

        elif showCurrent and (not areShown):

            self.__widgets.AddGroup('currentSettings',
                                    strings.labels[self, 'currentSettings'])

            colour    = props.makeWidget(widgets, tsPanel, 'currentColour')
            alpha     = props.makeWidget(widgets, tsPanel, 'currentAlpha',
                                         showLimits=False, spin=False)
            lineWidth = props.makeWidget(widgets, tsPanel, 'currentLineWidth')
            lineStyle = props.makeWidget(
                widgets,
                tsPanel,
                'currentLineStyle',
                labels=strings.choices['DataSeries.lineStyle'])

            self.__widgets.AddWidget(
                colour,
                displayName=strings.properties[tsPanel, 'currentColour'],
                tooltip=fsltooltips.properties[tsPanel, 'currentColour'],
                groupName='currentSettings')
            self.__widgets.AddWidget(
                alpha,
                displayName=strings.properties[tsPanel, 'currentAlpha'],
                tooltip=fsltooltips.properties[tsPanel, 'currentAlpha'],
                groupName='currentSettings')
            self.__widgets.AddWidget(
                lineWidth,
                displayName=strings.properties[tsPanel, 'currentLineWidth'],
                tooltip=fsltooltips.properties[tsPanel, 'currentLineWidth'],
                groupName='currentSettings') 
            self.__widgets.AddWidget(
                lineStyle,
                displayName=strings.properties[tsPanel, 'currentLineStyle'],
                tooltip=fsltooltips.properties[tsPanel, 'currentLineStyle'],
                groupName='currentSettings')
            

    def __selectedOverlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` property for the currently
        selected overlay changes. Only called if the current overlay is a
        :class:`.FEATImage`. Updates the display name of the *FEAT plot
        settings* section.
        """
        display = self._displayCtx.getDisplay(self.__selectedOverlay)
        self.__widgets.RenameGroup(
            'currentFEATSettings',
            strings.labels[self, 'currentFEATSettings'].format(
                display.name))

    
    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes. If the newly selected overlay is a
        :class:`.FEATImage`, the *FEAT plot settings* section is updated.
        """

        # We're assuminbg that the TimeSeriesPanel has
        # already updated its current TimeSeries for
        # the newly selected overlay.

        if self.__selectedOverlay is not None:
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self._name)
            self.__selectedOverlay = None

        if self.__widgets.HasGroup('currentFEATSettings'):
            self.__widgets.RemoveGroup('currentFEATSettings')

        ts = self.__tsPanel.getCurrent()

        if ts is None or not isinstance(ts, timeseries.FEATTimeSeries):
            return

        overlay = ts.overlay
        display = self._displayCtx.getDisplay(overlay)

        self.__selectedOverlay = overlay

        display.addListener('name',
                            self._name,
                            self.__selectedOverlayNameChanged)

        self.__widgets.AddGroup(
            'currentFEATSettings',
            displayName=strings.labels[self, 'currentFEATSettings'].format(
                display.name))

        full    = props.makeWidget(     self.__widgets, ts, 'plotFullModelFit')
        res     = props.makeWidget(     self.__widgets, ts, 'plotResiduals')
        evs     = props.makeListWidgets(self.__widgets, ts, 'plotEVs')
        pes     = props.makeListWidgets(self.__widgets, ts, 'plotPEFits')
        copes   = props.makeListWidgets(self.__widgets, ts, 'plotCOPEFits')
        partial = props.makeWidget(     self.__widgets, ts, 'plotPartial')
        data    = props.makeWidget(     self.__widgets, ts, 'plotData') 

        self.__widgets.AddWidget(
            data,
            displayName=strings.properties[ts, 'plotData'],
            tooltip=fsltooltips.properties[ts, 'plotData'],
            groupName='currentFEATSettings') 
        self.__widgets.AddWidget(
            full,
            displayName=strings.properties[ts, 'plotFullModelFit'],
            tooltip=fsltooltips.properties[ts, 'plotFullModelFit'],
            groupName='currentFEATSettings')
        
        self.__widgets.AddWidget(
            res,
            displayName=strings.properties[ts, 'plotResiduals'],
            tooltip=fsltooltips.properties[ts, 'plotResiduals'],
            groupName='currentFEATSettings')
        
        self.__widgets.AddWidget(
            partial,
            displayName=strings.properties[ts, 'plotPartial'],
            tooltip=fsltooltips.properties[ts, 'plotPartial'],
            groupName='currentFEATSettings')

        self.__widgets.AddSpace(groupName='currentFEATSettings')

        for i, ev in enumerate(evs):

            evName = ts.overlay.evNames()[i]
            self.__widgets.AddWidget(
                ev,
                displayName=strings.properties[ts, 'plotEVs'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotEVs'],
                groupName='currentFEATSettings')

        self.__widgets.AddSpace(groupName='currentFEATSettings')
            
        for i, pe in enumerate(pes):
            evName = ts.overlay.evNames()[i]
            self.__widgets.AddWidget(
                pe,
                displayName=strings.properties[ts, 'plotPEFits'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotPEFits'],
                groupName='currentFEATSettings')

        self.__widgets.AddSpace(groupName='currentFEATSettings')

        copeNames = overlay.contrastNames()
        for i, (cope, name) in enumerate(zip(copes, copeNames)):
            self.__widgets.AddWidget(
                cope,
                displayName=strings.properties[ts, 'plotCOPEFits'].format(
                    i + 1, name),
                tooltip=fsltooltips.properties[ts, 'plotCOPEFits'],
                groupName='currentFEATSettings') 
