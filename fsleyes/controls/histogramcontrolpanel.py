#!/usr/bin/env python
#
# histogramcontrolpanel.py - The HistogramControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramControlPanel` class, a *FSLeyes
control* panel which allows a :class:`.HistogramPanel` to be configured.
"""

import wx

import fsleyes_props                     as props
import fsleyes.tooltips                  as fsltooltips
import fsleyes.strings                   as strings
import fsleyes.plotting.histogramseries  as hseries
import fsleyes.views.histogrampanel      as histogrampanel
from . import                               plotcontrolpanel


class HistogramControlPanel(plotcontrolpanel.PlotControlPanel):
    """The ``HistogramControlPanel`` is a *FSLeyes control* panel which
    allows the user to configure a :class:`.HistogramPanel`. A
    ``HistogramControlPanel`` looks something like the following:

    .. image:: images/histogramcontrolpanel.png
       :scale: 50%
       :align: center
    """

    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.RIGHT}


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``HistogramControlPanel`` is only intended to be added to
        :class:`.HistogramPanel` views.
        """
        return [histogrampanel.HistogramPanel]


    def __init__(self, *args, **kwargs):
        """Create a ``HistogramControlPanel``. All arguments are passed
        through to the :meth:`.PlotControlPanel.__init__` method.
        """

        plotcontrolpanel.PlotControlPanel.__init__(self, *args, **kwargs)


    def generateCustomPlotPanelWidgets(self, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomPlotPanelWidgets`.
        Adds some widgets to control properties of the
        :class:`.HistogramPanel`.
        """

        hsPanel    = self.plotPanel
        widgetList = self.getWidgetList()
        allWidgets = []
        histProps  = ['histType', 'plotType']

        for prop in histProps:

            kwargs = {}

            kwargs['labels'] = strings.choices[hsPanel, prop]

            widget = props.makeWidget(widgetList, hsPanel, prop, **kwargs)
            allWidgets.append(widget)
            widgetList.AddWidget(
                widget,
                displayName=strings.properties[hsPanel, prop],
                tooltip=fsltooltips.properties[hsPanel, prop],
                groupName=groupName)

        return allWidgets


    def generateCustomDataSeriesWidgets(self, hs, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomDataSeriesWidgets`.
        Adds some widgets to control properties of the
        :class:`.HistogramSeries`.
        """

        isimage    = isinstance(hs, hseries.ImageHistogramSeries)
        widgetList = self.getWidgetList()
        allWidgets = []

        autoBin    = props.Widget('autoBin')
        nbins      = props.Widget('nbins',
                                  enabledWhen=lambda i: not i.autoBin,
                                  showLimits=False)
        autoBin    = props.buildGUI(widgetList, hs, autoBin)
        nbins      = props.buildGUI(widgetList, hs, nbins)

        dataRange = props.makeWidget(
            widgetList, hs, 'dataRange',
            labels=[strings.choices['HistogramPanel.dataRange.min'],
                    strings.choices['HistogramPanel.dataRange.max']],
            showLimits=False)

        ignoreZeros     = props.makeWidget(widgetList, hs, 'ignoreZeros')
        includeOutliers = props.makeWidget(widgetList, hs, 'includeOutliers')

        widgetList.AddWidget(ignoreZeros,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'ignoreZeros'],
                             tooltip=fsltooltips.properties[hs, 'ignoreZeros'])
        allWidgets.append(ignoreZeros)

        if isimage:
            showOverlay = props.makeWidget(widgetList, hs, 'showOverlay')
            widgetList.AddWidget(
                showOverlay,
                groupName=groupName,
                displayName=strings.properties[hs, 'showOverlay'],
                tooltip=fsltooltips.properties[hs, 'showOverlay'])
            allWidgets.append(showOverlay)

        widgetList.AddWidget(includeOutliers,
                             groupName=groupName,
                             displayName=strings.properties[hs,
                                                            'includeOutliers'],
                             tooltip=fsltooltips.properties[hs,
                                                            'includeOutliers'])
        widgetList.AddWidget(autoBin,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'autoBin'],
                             tooltip=fsltooltips.properties[hs, 'autoBin'])
        widgetList.AddWidget(nbins,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'nbins'],
                             tooltip=fsltooltips.properties[hs, 'nbins'])
        widgetList.AddWidget(dataRange,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'dataRange'],
                             tooltip=fsltooltips.properties[hs, 'dataRange'])
        allWidgets.append(includeOutliers)
        allWidgets.append(autoBin)
        allWidgets.append(nbins)
        allWidgets.append(dataRange)

        if isinstance(hs, hseries.ComplexHistogramSeries):
            for propName in ['plotReal', 'plotImaginary',
                             'plotMagnitude', 'plotPhase']:
                widget = props.makeWidget(widgetList, hs, propName)
                widgetList.AddWidget(
                    widget,
                    groupName=groupName,
                    displayName=strings.properties[hs, propName],
                    tooltip=fsltooltips.properties[hs, propName])
                allWidgets.append(widget)

        return allWidgets
