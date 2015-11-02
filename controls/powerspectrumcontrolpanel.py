#!/usr/bin/env python
#
# powerspectrumcontrolpanel.py - The PowerSpectrumControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumControlPanel` class.
"""


import                                             props

import fsl.fsleyes.controls.plotcontrolpanel    as plotcontrolpanel
import fsl.fsleyes.tooltips                     as fsltooltips
import fsl.fsleyes.plotting.powerspectrumseries as powerspectrumseries
import fsl.data.strings                         as strings


class PowerSpectrumControlPanel(plotcontrolpanel.PlotControlPanel):
    
    def __init__(self, *args, **kwargs):
        
        plotcontrolpanel.PlotControlPanel.__init__(self, *args, **kwargs)

        psPanel = self.getPlotPanel()
        psPanel.addListener('plotMelodicICs',
                            self._name,
                            self.__plotMelodicICsChanged)

    def destroy(self):
        psPanel = self.getPlotPanel()
        psPanel.removeListener('plotMelodicICs', self._name)
        plotcontrolpanel.PlotControlPanel.destroy(self)


    def generateCustomPlotPanelWidgets(self, groupName):

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
        """Called by the :meth:`__selectedOverlayChanged` method. Refreshes
        the *Settings for the current power spectrum* section, for the given
        :class:`.PowerSpectrumSeries` instance.
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
        """Called when the :attr:`.TimeSeriesPanel.plotMelodicICs` property
        changes. If the current overlay is a :class:`.MelodicImage`,
        re-generates the widgets in the *current time course* section, as
        the :class:`.TimeSeries` instance associated with the overlay may
        have been re-created.
        """
        self.refreshDataSeriesWidgets()
