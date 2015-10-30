#!/usr/bin/env python
#
# powerspectrumcontrolpanel.py - The PowerSpectrumControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumControlPanel` class.
"""


import wx

import                           props
import pwidgets.widgetlist    as widgetlist

import fsl.fsleyes.panel      as fslpanel
import fsl.fsleyes.tooltips   as fsltooltips
import fsl.data.strings       as strings
import timeseriescontrolpanel as tscontrol


class PowerSpectrumControlPanel(fslpanel.FSLEyesPanel):
    
    def __init__(self, parent, overlayList, displayCtx, psPanel):
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)
        
        self.__psPanel = psPanel
        self.__widgets = widgetlist.WidgetList(self)
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        psProps = ['showMode',
                   'plotFrequencies',
                   'plotMelodicICs']
        
        self.__widgets.AddGroup(
            'psSettings', strings.labels[self, 'psSettings'])

        for prop in psProps:
            
            kwargs = {}
            
            if prop == 'showMode':
                kwargs['labels'] = strings.choices[psPanel, 'showMode']
                
            widget = props.makeWidget(self.__widgets, psPanel, prop, **kwargs)
            
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[psPanel, prop],
                tooltip=fsltooltips.properties[psPanel, prop],
                groupName='psSettings')

        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[psPanel, 'plotSettings'])
            
        tscontrol.generatePlotPanelWidgets(psPanel,
                                           self.__widgets,
                                           'plotSettings') 
