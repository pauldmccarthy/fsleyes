#!/usr/bin/env python
#
# powerspectrumcontrolpanel.py - The PowerSpectrumControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumControlPanel` class, a
*FSLeyes control* panel for controlling a :class:`.PowerSpectrumPanel`.
"""


import fsleyes_props                        as props

import fsleyes.tooltips                     as fsltooltips
import fsleyes.plotting.powerspectrumseries as powerspectrumseries
import fsleyes.strings                      as strings
from . import plotcontrolpanel              as plotcontrol


class PowerSpectrumControlPanel(plotcontrol.PlotControlPanel):
    """The ``PowerSpectrumControlPanel`` class is a :class:`.PlotControlPanel`
    which allows the user to control a :class:`.PowerSpectrumPanel`.
    """

    def __init__(self, *args, **kwargs):
        """Create a ``PowerSpectrumControlPanel``. All arguments are passed
        through to the :meth:`.PlotControlPanel.__init__` method.
        """

        plotcontrol.PlotControlPanel.__init__(self, *args, **kwargs)

        psPanel = self.getPlotPanel()
        psPanel.addListener('plotMelodicICs',
                            self._name,
                            self.__plotMelodicICsChanged)


    def destroy(self):
        """Must be called when this ``PowerSpectrumControlPanel`` is no
        longer needed. Removes some property listeners and calls the
        :meth:`.PlotControlPanel.destroy` method.
        """
        psPanel = self.getPlotPanel()
        psPanel.removeListener('plotMelodicICs', self._name)
        plotcontrol.PlotControlPanel.destroy(self)


    def generateCustomPlotPanelWidgets(self, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomPlotPanelWidgets`.

        Adds some widgets for controlling the :class:`.PowerSpectrumPanel`.
        """

        psPanel    = self.getPlotPanel()
        widgetList = self.getWidgetList()
        allWidgets = []
        psProps    = ['plotFrequencies',
                      'plotMelodicICs']

        for prop in psProps:

            kwargs = {}

            widget = props.makeWidget(widgetList, psPanel, prop, **kwargs)
            allWidgets.append(widget)
            widgetList.AddWidget(
                widget,
                displayName=strings.properties[psPanel, prop],
                tooltip=fsltooltips.properties[psPanel, prop],
                groupName=groupName)

        return allWidgets


    def generateDataSeriesWidgets(self, ps, groupName):
        """Overrides :meth:`.PlotControlPanel.generateDataSeriesWidgets`.
        Adds some widgets for controlling :class:`.PowerSpectrumSeries`
        instances.
        """
        allWidgets = plotcontrol.PlotControlPanel.generateDataSeriesWidgets(
            self, ps, groupName)

        if not isinstance(ps, powerspectrumseries.PowerSpectrumSeries):
            return

        widgetList = self.getWidgetList()
        varNorm    = props.makeWidget(widgetList, ps, 'varNorm')

        widgetList.AddWidget(varNorm,
                             displayName=strings.properties[ps, 'varNorm'],
                             tooltip=strings.properties[ps, 'varNorm'],
                             groupName=groupName)

        return allWidgets + [varNorm]


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`.PowerSpectrumPanel.plotMelodicICs` property
        changes. Calls :meth:`.PlotControlPanel.refreshDataSeriesWidgets` to
        ensure that the displayed widgets are linked to the correct
        :class:`.PowerSpectrumSeries` instance.
        """
        self.refreshDataSeriesWidgets()
