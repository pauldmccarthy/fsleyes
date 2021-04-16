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

import fsleyes_props                 as props
import fsl.data.image                as fslimage
import fsl.data.featimage            as fslfeatimage

import fsleyes.tooltips              as fsltooltips
import fsleyes.plotting.timeseries   as timeseries
import fsleyes.strings               as strings
import fsleyes.views.timeseriespanel as timeseriespanel
from . import plotcontrolpanel       as plotctrl


class TimeSeriesControlPanel(plotctrl.PlotControlPanel):
    """The ``TimeSeriesControlPanel`` is a :class:`.PlotContrlPanel` which
    allows the user to configure a :class:`.TimeSeriesPanel`. It contains
    controls which are linked to the properties of the ``TimeSeriesPanel``,
    (which include properties defined on the :class:`.PlotPanel` base class),
    and the :class:`.DataSeries` class.


    A ``TimeSeriesControlPanel`` looks something like this:

    .. image:: images/timeseriescontrolpanel.png
       :scale: 50%
       :align: center


    The settings shown on a ``TimeSeriesControlPanel`` are organised into three
    or four sections:

     - The *Time series plot settings* section has controls which are linked to
       properties of the :class:`.PlotCanvas` class.

     - The *General plot settings* section has controls which are linked to
       properties of the :class:`.PlotPanel` base class.

     - The *Settings for the current time course* section has controls which
       are linked to properties of the :class:`.DataSeries` class. These
       properties define how the *current* time course is displayed (see the
       :class:`.TimeSeriesPanel` class documentation).

     - The *FEAT plot settings* is only shown if the currently selected overlay
       is a :class:`.FEATImage`. It has controls which are linked to properties
       of the :class:`.FEATTimeSeries` class.
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``TimeSeriesControlPanel`` is only intended to be added to
        :class:`.TimeSeriesPanel` views.
        """

        return [timeseriespanel.TimeSeriesPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.RIGHT}


    def __init__(self, *args, **kwargs):
        """Create a ``TimeSeriesControlPanel``. All arguments are passed
        through to the :meth:`.PlotControlPanel.__init__` method.
        """

        plotctrl.PlotControlPanel.__init__(self, *args, **kwargs)

        self.plotPanel.addListener('plotMelodicICs',
                                   self.name,
                                   self.__plotMelodicICsChanged)


    def destroy(self):
        """Must be called when this ``TimeSeriesControlPanel`` is no longer
        needed. Removes some property listeners, and calls
        :meth:`.PlotControlPanel.destroy`.
        """
        psPanel = self.getPlotPanel()
        psPanel.removeListener('plotMelodicICs', self.name)
        plotctrl.PlotControlPanel.destroy(self)


    def generateCustomPlotPanelWidgets(self, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomPlotPanelWidgets`.

        Adds some widgets for controlling some properties of the
        :class:`.TimeSeriesPanel`.
        """

        widgetList = self.getWidgetList()
        allWidgets = []
        tsPanel    = self.plotPanel
        tsProps    = ['plotMode',
                      'usePixdim',
                      'plotMelodicICs']

        for prop in tsProps:
            kwargs = {}
            if prop == 'plotMode':
                kwargs['labels'] = strings.choices[tsPanel, 'plotMode']

            widget = props.makeWidget(widgetList, tsPanel, prop, **kwargs)
            allWidgets.append(widget)
            widgetList.AddWidget(
                widget,
                displayName=strings.properties[tsPanel, prop],
                tooltip=fsltooltips.properties[tsPanel, prop],
                groupName=groupName)

        return allWidgets


    def generateCustomDataSeriesWidgets(self, ts, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomDataSeriesWidgets`.

        Adds some widgets to the widget list for certain time series types.
        """

        overlay = ts.overlay

        if (isinstance(overlay, fslfeatimage.FEATImage)    and
            isinstance(ts,      timeseries.FEATTimeSeries) and
            overlay.hasStats()):
            return self.__generateFeatWidgets(ts, groupName)

        elif isinstance(ts, timeseries.ComplexTimeSeries):
            return self.__generateComplexWidgets(ts, groupName)

        else:
            return []


    def __generateFeatWidgets(self, ts, groupName):
        """Called by :meth:`generateCustomDataSeriesWidgets`. Generates
        widgets for :class:`.FEATTimeSeries` options, and adds them
        to the widget list.
        """

        overlay    = ts.overlay
        widgetList = self.getWidgetList()
        allWidgets = []

        full    = props.makeWidget(     widgetList, ts, 'plotFullModelFit')
        res     = props.makeWidget(     widgetList, ts, 'plotResiduals')
        evs     = props.makeListWidgets(widgetList, ts, 'plotEVs')
        pes     = props.makeListWidgets(widgetList, ts, 'plotPEFits')
        copes   = props.makeListWidgets(widgetList, ts, 'plotCOPEFits')
        partial = props.makeWidget(     widgetList, ts, 'plotPartial')
        data    = props.makeWidget(     widgetList, ts, 'plotData')

        allWidgets.append(full)
        allWidgets.append(res)
        allWidgets.extend(evs)
        allWidgets.extend(pes)
        allWidgets.extend(copes)
        allWidgets.append(partial)
        allWidgets.append(data)

        widgetList.AddWidget(
            data,
            displayName=strings.properties[ts, 'plotData'],
            tooltip=fsltooltips.properties[ts, 'plotData'],
            groupName=groupName)
        widgetList.AddWidget(
            full,
            displayName=strings.properties[ts, 'plotFullModelFit'],
            tooltip=fsltooltips.properties[ts, 'plotFullModelFit'],
            groupName=groupName)

        widgetList.AddWidget(
            res,
            displayName=strings.properties[ts, 'plotResiduals'],
            tooltip=fsltooltips.properties[ts, 'plotResiduals'],
            groupName=groupName)

        widgetList.AddWidget(
            partial,
            displayName=strings.properties[ts, 'plotPartial'],
            tooltip=fsltooltips.properties[ts, 'plotPartial'],
            groupName=groupName)

        widgetList.AddSpace(groupName=groupName)

        for i, ev in enumerate(evs):

            evName = overlay.evNames()[i]
            widgetList.AddWidget(
                ev,
                displayName=strings.properties[ts, 'plotEVs'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotEVs'],
                groupName=groupName)

        widgetList.AddSpace(groupName=groupName)

        for i, pe in enumerate(pes):
            evName = overlay.evNames()[i]
            widgetList.AddWidget(
                pe,
                displayName=strings.properties[ts, 'plotPEFits'].format(
                    i + 1, evName),
                tooltip=fsltooltips.properties[ts, 'plotPEFits'],
                groupName=groupName)

        widgetList.AddSpace(groupName=groupName)

        copeNames = overlay.contrastNames()
        for i, (cope, name) in enumerate(zip(copes, copeNames)):
            widgetList.AddWidget(
                cope,
                displayName=strings.properties[ts, 'plotCOPEFits'].format(
                    i + 1, name),
                tooltip=fsltooltips.properties[ts, 'plotCOPEFits'],
                groupName=groupName)

        return allWidgets


    def __generateComplexWidgets(self, ts, groupName):
        """Called by :meth:`generateCustomDataSeriesWidgets`. Generates
        widgets for :class:`.ComplexTimeSeries` options, and adds them
        to the widget list.
        """
        widgetList = self.getWidgetList()
        allWidgets = []

        if isinstance(ts, timeseries.ComplexTimeSeries):
            for propName in ['plotReal', 'plotImaginary',
                             'plotMagnitude', 'plotPhase']:
                widg = props.makeWidget(widgetList, ts, propName)
                widgetList.AddWidget(
                    widg,
                    displayName=strings.properties[ts, propName],
                    tooltip=fsltooltips.properties[ts, propName],
                    groupName=groupName)
                allWidgets.append(widg)

        return allWidgets


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`.TimeSeriesPanel.plotMelodicICs` property
        changes. If the current overlay is a :class:`.MelodicImage`,
        re-generates the widgets in the *current time course* section, as
        the :class:`.DataSeries` instance associated with the overlay may
        have been re-created.
        """
        self.refreshDataSeriesWidgets()
