#!/usr/bin/env python
#
# lightboxtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx

import props

import fsl.fsleyes.toolbar as fsltoolbar
import fsl.fsleyes.actions as actions
import fsl.fsleyes.icons   as icons
import fsl.data.strings    as strings


class LightBoxToolBar(fsltoolbar.FSLEyesToolBar):

    def __init__(self, parent, overlayList, displayCtx, lb):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLEyesToolBar.__init__(
            self, parent, overlayList, displayCtx, 24, actionz)
        self.lightBoxPanel = lb

        icns = {
            'screenshot'  : icons.findImageFile('camera24'),
            'more'        : icons.findImageFile('gear24'),

            'zax' : {
                0 : icons.findImageFile('sagittalSlice24'),
                1 : icons.findImageFile('coronalSlice24'),
                2 : icons.findImageFile('axialSlice24'),
            }
        }

        sceneOpts = lb.getSceneOptions()
        
        specs = {
            
            'more'       : actions.ActionButton('more',
                                                icon=icns['more']),
            'screenshot' : actions.ActionButton('screenshot',
                                                icon=icns['screenshot']),
            
            'zax'          : props.Widget(
                'zax',
                icons=icns['zax']),
            
            'sliceSpacing' : props.Widget(
                'sliceSpacing',
                spin=False,
                showLimits=False),
            
            'zrange'       : props.Widget(
                'zrange',
                spin=False,
                showLimits=False,
                labels=[strings.choices[sceneOpts, 'zrange', 'min'],
                        strings.choices[sceneOpts, 'zrange', 'max']]),
            
            'zoom'         : props.Widget(
                'zoom',
                spin=False,
                showLimits=False),
        }

        # Slice spacing and zoom go on a single panel
        panel = wx.Panel(self)
        sizer = wx.FlexGridSizer(2, 2)
        panel.SetSizer(sizer)

        more         = props.buildGUI(self,  self,      specs['more'])
        screenshot   = props.buildGUI(self,  lb,        specs['screenshot'])
        zax          = props.buildGUI(self,  sceneOpts, specs['zax'])
        zrange       = props.buildGUI(self,  sceneOpts, specs['zrange'])
        zoom         = props.buildGUI(panel, sceneOpts, specs['zoom'])
        spacing      = props.buildGUI(panel, sceneOpts, specs['sliceSpacing'])
        zoomLabel    = wx.StaticText(panel)
        spacingLabel = wx.StaticText(panel)

        zoomLabel   .SetLabel(strings.properties[sceneOpts, 'zoom'])
        spacingLabel.SetLabel(strings.properties[sceneOpts, 'sliceSpacing'])

        sizer.Add(zoomLabel)
        sizer.Add(zoom,    flag=wx.EXPAND)
        sizer.Add(spacingLabel)
        sizer.Add(spacing, flag=wx.EXPAND)

        tools = [more, screenshot, zax, zrange, panel]
        
        self.SetTools(tools) 

        
    def showMoreSettings(self, *a):
        import canvassettingspanel
        self.lightBoxPanel.togglePanel(
            canvassettingspanel.CanvasSettingsPanel,
            self.lightBoxPanel,
            floatPane=True) 
