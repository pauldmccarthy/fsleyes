#!/usr/bin/env python
#
# powerspectrumcontrolpanel.py - The PowerSpectrumControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumControlPanel` class, a
*FSLeyes control* panel for controlling a :class:`.PowerSpectrumPanel`.
"""


import                                             props

import                                             plotcontrolpanel
import fsl.fsleyes.tooltips                     as fsltooltips
import fsl.fsleyes.plotting.powerspectrumseries as powerspectrumseries
import fsl.data.strings                         as strings


class PowerSpectrumControlPanel(plotcontrolpanel.PlotControlPanel):
    """The ``PowerSpectrumControlPanel`` class is a :class:`.PlotControlPanel`
    which allows the user to control a :class:`.PowerSpectrumPanel`.
    """
    
    def __init__(self, *args, **kwargs):
        """Create a ``PowerSpectrumControlPanel``. All arguments are passed
        through to the :meth:`.PlotControlPanel.__init__` method.
        """
        
        plotcontrolpanel.PlotControlPanel.__init__(self, *args, **kwargs)

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
        plotcontrolpanel.PlotControlPanel.destroy(self)


    def generateCustomPlotPanelWidgets(self, groupName):
        """Overrides :meth:`.PlotControlPanel.generateCustomPlotPanelWidgets`.

        Adds some widgets for controlling the :class:`.PowerSpectrumPanel`.
        """
        
        psPanel = self.getPlotPanel()
        widgets = self.getWidgetList()
        psProps = ['showMode',
                   'plotFrequencies',
                   'plotMelodicICs']
        
        for prop in psProps:
            
            kwargs = {}
            
            if prop == 'showMode':
                kwargs['labels'] = strings.choices[psPanel, 'showMode']
                
            widget = props.makeWidget(widgets, psPanel, prop, **kwargs)
            
            widgets.AddWidget(
                widget,
                displayName=strings.properties[psPanel, prop],
                tooltip=fsltooltips.properties[psPanel, prop],
                groupName=groupName)


    def generateDataSeriesWidgets(self, ps, groupName):
        """Overrides :meth:`.PlotControlPanel.generateDataSeriesWidgets`.
        Adds some widgets for controlling :class:`.PowerSpectrumSeries`
        instances.
        """
        plotcontrolpanel.PlotControlPanel.generateDataSeriesWidgets(
            self, ps, groupName)

        if not isinstance(ps, powerspectrumseries.PowerSpectrumSeries):
            return
        
        widgets = self.getWidgetList()
        varNorm = props.makeWidget(widgets, ps, 'varNorm')

        widgets.AddWidget(varNorm,
                          displayName=strings.properties[ps, 'varNorm'],
                          tooltip=strings.properties[ps, 'varNorm'],
                          groupName=groupName)

        
    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`.PowerSpectrumPanel.plotMelodicICs` property
        changes. Calls :meth:`.PlotControlPanel.refreshDataSeriesWidgets` to
        ensure that the displayed widgets are linked to the correct
        :class:`.PowerSpectrumSeries` instance.
        """
        self.refreshDataSeriesWidgets()
