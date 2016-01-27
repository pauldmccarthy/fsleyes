#!/usr/bin/env python
#
# timeseriescontrolpanel.py - The TimeSeriesControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesControlPanel` a *FSLeyes
control* which allows the user to configure a :class:`.TimeSeriesPanel`.
"""


import                                    props

import                                    plotcontrolpanel
import fsl.fsleyes.tooltips            as fsltooltips
import fsl.fsleyes.plotting.timeseries as timeseries
import fsl.data.featimage              as fslfeatimage
import fsl.data.strings                as strings


class TimeSeriesControlPanel(plotcontrolpanel.PlotControlPanel):
    """The ``TimeSeriesControlPanel`` is a :class:`.PlotContrlPanel` which
    allows the user to configure a :class:`.TimeSeriesPanel`. It contains
    controls which are linked to the properties of the ``TimeSeriesPanel``,
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

    
    def __init__(self, *args, **kwargs):
        """Create a ``TimeSeriesControlPanel``. All arguments are passed
        through to the :meth:`.PlotControlPanel.__init__` method.
        """

        plotcontrolpanel.PlotControlPanel.__init__(self, *args, **kwargs)

        tsPanel = self.getPlotPanel()
        tsPanel.addListener('plotMelodicICs',
                            self._name,
                            self.__plotMelodicICsChanged)

        
    def destroy(self):
        """Must be called when this ``TimeSeriesControlPanel`` is no longer
        needed. Removes some property listeners, and calls
        :meth:`.PlotControlPanel.destroy`.
        """
        psPanel = self.getPlotPanel()
        psPanel.removeListener('plotMelodicICs', self._name)
        plotcontrolpanel.PlotControlPanel.destroy(self) 


    def generateCustomPlotPanelWidgets(self, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomPlotPanelWidgets`.

        Adds some widgets for controlling some properties of the
        :class:`.TimeSeriesPanel`.
        """

        widgets = self.getWidgetList()
        tsPanel = self.getPlotPanel()
        tsProps = ['showMode',
                   'plotMode',
                   'usePixdim',
                   'plotMelodicICs']

        for prop in tsProps:
            kwargs = {}
            if prop == 'plotMode':
                kwargs['labels'] = strings.choices[tsPanel, 'plotMode']
            elif prop == 'showMode':
                kwargs['labels'] = strings.choices[tsPanel, 'showMode']
                
            widget = props.makeWidget(widgets, tsPanel, prop, **kwargs)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[tsPanel, prop],
                tooltip=fsltooltips.properties[tsPanel, prop],
                groupName=groupName)


    def generateCustomDataSeriesWidgets(self, ts, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomDataSeriesWidgets`.

        If the given :class:`.TimeSeries` is a :class:`.FEATTimeSeries`
        instance, this method adds some widgets for controlling the
        FEAT-related settings of the instance.
        """

        overlay = ts.overlay
        widgets = self.getWidgetList()

        if not (isinstance(overlay, fslfeatimage.FEATImage)    and
                isinstance(ts,      timeseries.FEATTimeSeries) and
                overlay.hasStats()):
            return

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
            groupName=groupName)
        widgets.AddWidget(
            full,
            displayName=strings.properties[ts, 'plotFullModelFit'],
            tooltip=fsltooltips.properties[ts, 'plotFullModelFit'],
            groupName=groupName)
        
        widgets.AddWidget(
            res,
            displayName=strings.properties[ts, 'plotResiduals'],
            tooltip=fsltooltips.properties[ts, 'plotResiduals'],
            groupName=groupName)
        
        widgets.AddWidget(
            partial,
            displayName=strings.properties[ts, 'plotPartial'],
            tooltip=fsltooltips.properties[ts, 'plotPartial'],
            groupName=groupName)

        widgets.AddSpace(groupName=groupName)

        for i, ev in enumerate(evs):

            evName = overlay.evNames()[i]
            widgets.AddWidget(
                ev,
                displayName=strings.properties[ts, 'plotEVs'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotEVs'],
                groupName=groupName)

        widgets.AddSpace(groupName=groupName)
            
        for i, pe in enumerate(pes):
            evName = overlay.evNames()[i]
            widgets.AddWidget(
                pe,
                displayName=strings.properties[ts, 'plotPEFits'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotPEFits'],
                groupName=groupName)

        widgets.AddSpace(groupName=groupName)

        copeNames = overlay.contrastNames()
        for i, (cope, name) in enumerate(zip(copes, copeNames)):
            widgets.AddWidget(
                cope,
                displayName=strings.properties[ts, 'plotCOPEFits'].format(
                    i + 1, name),
                tooltip=fsltooltips.properties[ts, 'plotCOPEFits'],
                groupName=groupName) 


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`.TimeSeriesPanel.plotMelodicICs` property
        changes. If the current overlay is a :class:`.MelodicImage`,
        re-generates the widgets in the *current time course* section, as
        the :class:`.TimeSeries` instance associated with the overlay may
        have been re-created.
        """
        self.refreshDataSeriesWidgets()
