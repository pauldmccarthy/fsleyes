#!/usr/bin/env python
#
# histogramcontrolpanel.py - The HistogramControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramControlPanel` class, a *FSLeyes
control* panel which allows a :class:`.HistogramPanel` to be configured.
"""


import                     props

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

        hsPanel   = self.getPlotPanel()
        widgets   = self.getWidgetList()
        histProps = ['histType']

        for prop in histProps:

            kwargs = {}

            if prop == 'histType':
                kwargs['labels'] = strings.choices[hsPanel, 'histType']

            widget = props.makeWidget(widgets, hsPanel, prop, **kwargs)
            
            widgets.AddWidget(
                widget,
                displayName=strings.properties[hsPanel, prop],
                tooltip=fsltooltips.properties[hsPanel, prop],
                groupName=groupName)


    def generateCustomDataSeriesWidgets(self, hs, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomDataSeriesWidgets`.
        Adds some widgets to control properties of the
        :class:`.HistogramSeries`.
        """

        def is4D(h):
            return len(h.overlay.shape) == 4 and h.overlay.shape[3] > 1
        
        widgets    = self.getWidgetList()

        volume     = props.Widget('volume',
                                  showLimits=False,
                                  enabledWhen=is4D)
        autoBin    = props.Widget('autoBin')
        nbins      = props.Widget('nbins',
                                  enabledWhen=lambda i: not i.autoBin,
                                  showLimits=False)

        volume     = props.buildGUI(widgets, hs, volume)
        autoBin    = props.buildGUI(widgets, hs, autoBin)
        nbins      = props.buildGUI(widgets, hs, nbins)
        
        dataRange = props.makeWidget(
            widgets, hs, 'dataRange',
            labels=[strings.choices['HistogramPanel.dataRange.min'],
                    strings.choices['HistogramPanel.dataRange.max']],
            showLimits=False)
        
        ignoreZeros     = props.makeWidget(widgets, hs, 'ignoreZeros')
        showOverlay     = props.makeWidget(widgets, hs, 'showOverlay')
        includeOutliers = props.makeWidget(widgets, hs, 'includeOutliers')

        widgets.AddWidget(ignoreZeros,
                          groupName=groupName,
                          displayName=strings.properties[hs, 'ignoreZeros'],
                          tooltip=fsltooltips.properties[hs, 'ignoreZeros'])
        widgets.AddWidget(showOverlay,
                          groupName=groupName,
                          displayName=strings.properties[hs, 'showOverlay'],
                          tooltip=fsltooltips.properties[hs, 'showOverlay'])
        widgets.AddWidget(includeOutliers,
                          groupName=groupName,
                          displayName=strings.properties[hs,
                                                         'includeOutliers'],
                          tooltip=fsltooltips.properties[hs,
                                                         'includeOutliers'])
        widgets.AddWidget(autoBin,
                          groupName=groupName,
                          displayName=strings.properties[hs, 'autoBin'],
                          tooltip=fsltooltips.properties[hs, 'autoBin']) 
        widgets.AddWidget(nbins,
                          groupName=groupName,
                          displayName=strings.properties[hs, 'nbins'],
                          tooltip=fsltooltips.properties[hs, 'nbins'])
        widgets.AddWidget(volume,
                          groupName=groupName,
                          displayName=strings.properties[hs, 'volume'],
                          tooltip=fsltooltips.properties[hs, 'volume'])
        widgets.AddWidget(dataRange,
                          groupName=groupName,
                          displayName=strings.properties[hs, 'dataRange'],
                          tooltip=fsltooltips.properties[hs, 'dataRange'])
