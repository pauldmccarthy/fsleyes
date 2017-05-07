#!/usr/bin/env python
#
# histogramcontrolpanel.py - The HistogramControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramControlPanel` class, a *FSLeyes
control* panel which allows a :class:`.HistogramPanel` to be configured.
"""


import fsleyes_props    as props

import fsleyes.tooltips as fsltooltips
import fsleyes.strings  as strings
from . import              plotcontrolpanel


class HistogramControlPanel(plotcontrolpanel.PlotControlPanel):
    """The ``HistogramControlPanel`` is a *FSLeyes control* panel which
    allows the user to configure a :class:`.HistogramPanel`. A
    ``HistogramControlPanel`` looks something like the following:

    .. image:: images/histogramcontrolpanel.png
       :scale: 50%
       :align: center
    """


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

        hsPanel    = self.getPlotPanel()
        widgetList = self.getWidgetList()
        allWidgets = []
        histProps  = ['histType']

        for prop in histProps:

            kwargs = {}

            if prop == 'histType':
                kwargs['labels'] = strings.choices[hsPanel, 'histType']

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

        def is4D(h):
            return len(h.overlay.shape) == 4 and h.overlay.shape[3] > 1

        widgetList = self.getWidgetList()

        volume     = props.Widget('volume',
                                  showLimits=False,
                                  enabledWhen=is4D)
        autoBin    = props.Widget('autoBin')
        nbins      = props.Widget('nbins',
                                  enabledWhen=lambda i: not i.autoBin,
                                  showLimits=False)

        volume     = props.buildGUI(widgetList, hs, volume)
        autoBin    = props.buildGUI(widgetList, hs, autoBin)
        nbins      = props.buildGUI(widgetList, hs, nbins)

        dataRange = props.makeWidget(
            widgetList, hs, 'dataRange',
            labels=[strings.choices['HistogramPanel.dataRange.min'],
                    strings.choices['HistogramPanel.dataRange.max']],
            showLimits=False)

        ignoreZeros     = props.makeWidget(widgetList, hs, 'ignoreZeros')
        showOverlay     = props.makeWidget(widgetList, hs, 'showOverlay')
        includeOutliers = props.makeWidget(widgetList, hs, 'includeOutliers')

        widgetList.AddWidget(ignoreZeros,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'ignoreZeros'],
                             tooltip=fsltooltips.properties[hs, 'ignoreZeros'])
        widgetList.AddWidget(showOverlay,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'showOverlay'],
                             tooltip=fsltooltips.properties[hs, 'showOverlay'])
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
        widgetList.AddWidget(volume,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'volume'],
                             tooltip=fsltooltips.properties[hs, 'volume'])
        widgetList.AddWidget(dataRange,
                             groupName=groupName,
                             displayName=strings.properties[hs, 'dataRange'],
                             tooltip=fsltooltips.properties[hs, 'dataRange'])

        return [ignoreZeros,
                showOverlay,
                includeOutliers,
                autoBin,
                nbins,
                volume,
                dataRange]
