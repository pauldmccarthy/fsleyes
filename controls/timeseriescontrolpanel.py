#!/usr/bin/env python
#
# timeseriescontrolpanel.py - The TimeSeriesControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesControlPanel` a *FSLeyes
control* which allows the user to configure a :class:`.TimeSeriesPanel`.


This module also provides a couple of general functions which generate widgets
for :class:`.PlotPanel` and :class:`.DataSeries` instances:

.. autosummary::
   :nosignatures:

   generatePlotPanelWidgets
   generateDataSeriesWidgets
"""


import wx

import                                    props
import pwidgets.widgetlist             as widgetlist

import fsl.fsleyes.panel               as fslpanel
import fsl.fsleyes.displaycontext      as fsldisplay
import fsl.fsleyes.plotting.timeseries as timeseries
import fsl.fsleyes.tooltips            as fsltooltips
import fsl.data.strings                as strings
import fsl.data.melodicimage           as fslmelimage


class TimeSeriesControlPanel(fslpanel.FSLEyesPanel):
    """The ``TimeSeriesControlPanel`` is a :class:`.FSLEyesPanel` which allows
    the user to configure a :class:`.TimeSeriesPanel`. It contains controls
    which are linked to the properties of the ``TimeSeriesPanel``,
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

        tsProps   = ['showMode',
                     'plotMode',
                     'usePixdim',
                     'plotMelodicICs']

        self.__widgets.AddGroup(
            'tsSettings',
            strings.labels[self, 'tsSettings'])

        for prop in tsProps:
            kwargs = {}
            if prop == 'plotMode':
                kwargs['labels'] = strings.choices['TimeSeriesPanel.plotMode']
            elif prop == 'showMode':
                kwargs['labels'] = strings.choices['TimeSeriesPanel.showMode']
                
            widget = props.makeWidget(self.__widgets, tsPanel, prop, **kwargs)
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[tsPanel, prop],
                tooltip=fsltooltips.properties[tsPanel, prop],
                groupName='tsSettings')

            
        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[tsPanel, 'plotSettings'])
            
        generatePlotPanelWidgets(tsPanel, self.__widgets, 'plotSettings')

        tsPanel    .addListener('plotMelodicICs',
                                self._name,
                                self.__plotMelodicICsChanged)
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


    def __selectedOverlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` property for the currently
        selected overlay changes. Updates the display name of the *FEAT plot
        settings* and *current time course* sections if necessary.
        """
        display = self._displayCtx.getDisplay(self.__selectedOverlay)
        
        if self.__widgets.HasGroup('currentFEATSettings'):
            self.__widgets.RenameGroup(
                'currentFEATSettings',
                strings.labels[self, 'currentFEATSettings'].format(
                    display.name))

        if self.__widgets.HasGroup('currentSettings'):
            self.__widgets.RenameGroup(
                'currentSettings',
                strings.labels[self, 'currentSettings'].format(display.name)) 

    
    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes. If the newly selected overlay is a
        :class:`.FEATImage`, the *FEAT plot settings* section is updated.
        """

        # We're assuminbg that the TimeSeriesPanel has
        # already updated its current TimeSeries for
        # the newly selected overlay.
        if self.__selectedOverlay is not None:
            try:
                display = self._displayCtx.getDisplay(self.__selectedOverlay)
                display.removeListener('name', self._name)
                
            # The overlay may have been
            # removed from the overlay list
            except fsldisplay.InvalidOverlayError:
                pass
                
            self.__selectedOverlay = None

        if self.__widgets.HasGroup('currentSettings'):
            self.__widgets.RemoveGroup('currentSettings') 
 
        if self.__widgets.HasGroup('currentFEATSettings'):
            self.__widgets.RemoveGroup('currentFEATSettings')

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ts = self.__tsPanel.getDataSeries(overlay)

        if ts is None:
            return

        self.__selectedOverlay = overlay

        display = self._displayCtx.getDisplay(overlay)

        display.addListener('name',
                            self._name,
                            self.__selectedOverlayNameChanged)

        self.__showSettingsForTimeSeries(ts)

        if isinstance(ts, timeseries.FEATTimeSeries):
            self.__showFEATSettingsForTimeSeries(ts)


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`.TimeSeriesPanel.plotMelodicICs` property
        changes. If the current overlay is a :class:`.MelodicImage`,
        re-generates the widgets in the *current time course* section, as
        the :class:`.TimeSeries` instance associated with the overlay may
        have been re-created.
        """

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        if not isinstance(overlay, fslmelimage.MelodicImage):
            return

        ts = self.__tsPanel.getTimeSeries(overlay)

        if ts is None:
            return

        if self.__widgets.HasGroup('currentSettings'):
            self.__widgets.RemoveGroup('currentSettings')

        self.__showSettingsForTimeSeries(ts)


    def __showFEATSettingsForTimeSeries(self, ts):
        """(Re-)crates the *FEAT settings* section for the given
        :class:`.FEATTimeSeries` instance.
        """

        overlay = ts.overlay
        display = self._displayCtx.getDisplay(overlay)
        widgets = self.__widgets

        widgets.AddGroup(
            'currentFEATSettings',
            displayName=strings.labels[self, 'currentFEATSettings'].format(
                display.name))

        full    = props.makeWidget(     widgets, ts, 'plotFullModelFit')
        res     = props.makeWidget(     widgets, ts, 'plotResiduals')
        evs     = props.makeListWidgets(widgets, ts, 'plotEVs')
        pes     = props.makeListWidgets(widgets, ts, 'plotPEFits')
        copes   = props.makeListWidgets(widgets, ts, 'plotCOPEFits')
        partial = props.makeWidget(     widgets, ts, 'plotPartial')
        data    = props.makeWidget(     widgets, ts, 'plotData') 

        widgets.AddWidget(
            data,
            displayName=strings.properties[ts, 'plotData'],
            tooltip=fsltooltips.properties[ts, 'plotData'],
            groupName='currentFEATSettings') 
        widgets.AddWidget(
            full,
            displayName=strings.properties[ts, 'plotFullModelFit'],
            tooltip=fsltooltips.properties[ts, 'plotFullModelFit'],
            groupName='currentFEATSettings')
        
        widgets.AddWidget(
            res,
            displayName=strings.properties[ts, 'plotResiduals'],
            tooltip=fsltooltips.properties[ts, 'plotResiduals'],
            groupName='currentFEATSettings')
        
        widgets.AddWidget(
            partial,
            displayName=strings.properties[ts, 'plotPartial'],
            tooltip=fsltooltips.properties[ts, 'plotPartial'],
            groupName='currentFEATSettings')

        widgets.AddSpace(groupName='currentFEATSettings')

        for i, ev in enumerate(evs):

            evName = overlay.evNames()[i]
            widgets.AddWidget(
                ev,
                displayName=strings.properties[ts, 'plotEVs'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotEVs'],
                groupName='currentFEATSettings')

        widgets.AddSpace(groupName='currentFEATSettings')
            
        for i, pe in enumerate(pes):
            evName = overlay.evNames()[i]
            widgets.AddWidget(
                pe,
                displayName=strings.properties[ts, 'plotPEFits'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotPEFits'],
                groupName='currentFEATSettings')

        widgets.AddSpace(groupName='currentFEATSettings')

        copeNames = overlay.contrastNames()
        for i, (cope, name) in enumerate(zip(copes, copeNames)):
            widgets.AddWidget(
                cope,
                displayName=strings.properties[ts, 'plotCOPEFits'].format(
                    i + 1, name),
                tooltip=fsltooltips.properties[ts, 'plotCOPEFits'],
                groupName='currentFEATSettings') 


    def __showSettingsForTimeSeries(self, ts):
        """Called by the :meth:`__selectedOverlayChanged` method. Refreshes
        the *Settings for the current time course* section, for the given
        :class:`.TimeSeries` instance.
        """
        overlay = ts.overlay
        display = self._displayCtx.getDisplay(overlay)
        widgets = self.__widgets

        self.__widgets.AddGroup(
            'currentSettings',
            strings.labels[self, 'currentSettings'].format(display.name))

        generateDataSeriesWidgets(ts, widgets, 'currentSettings')


def generatePlotPanelWidgets(plotPanel, widgetList, groupName):
    """Adds a collection of widgets to the given :class:`.WidgetList`,
    allowing the properties of the given :class:`.PlotPanel` instance
    to be changed.

    :arg plotPanel:  The :class:`.PlotPanel` instance. 
    :arg widgetList: The :class:`.WidgetList` instance.
    :arg groupName:  The ``WidgetList`` group name to use.
    """ 
    
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
                             label=strings.labels[plotPanel, 'xlabel']))
    labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
    labels.Add(wx.StaticText(widgetList,
                             label=strings.labels[plotPanel, 'ylabel']))
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
        displayName=strings.labels[plotPanel, 'labels'],
        tooltip=fsltooltips.misc[  plotPanel, 'labels'],
        groupName=groupName)
    widgetList.AddWidget(
        xlims,
        displayName=strings.labels[plotPanel, 'xlim'],
        tooltip=fsltooltips.misc[  plotPanel, 'xlim'],
        groupName=groupName)
    widgetList.AddWidget(
        ylims,
        displayName=strings.labels[plotPanel, 'ylim'],
        tooltip=fsltooltips.misc[  plotPanel, 'ylim'],
        groupName=groupName)

    
def generateDataSeriesWidgets(ds, widgetList, groupName):
    """Adds a collection of widgets to the given :class:`.WidgetList`,
    allowing the properties of the given :class:`.DataSeries` instance
    to be changed.

    :arg ds:         The :class:`.DataSeries` instance. 
    :arg widgetList: The :class:`.WidgetList` instance.
    :arg groupName:  The ``WidgetList`` group name to use.
    """
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
