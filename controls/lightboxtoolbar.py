#!/usr/bin/env python
#
# lightboxtoolbar.py - The LightBoxToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxToolBar` class, which is a
:class:`.FSLEyesToolBar` for use with the :class:`.LightBoxPanel`.
"""


import wx

import props

import fsl.fsleyes.toolbar  as fsltoolbar
import fsl.fsleyes.actions  as actions
import fsl.fsleyes.icons    as fslicons
import fsl.fsleyes.tooltips as fsltooltips
import fsl.data.strings     as strings
import fsl.data.image       as fslimage


class LightBoxToolBar(fsltoolbar.FSLEyesToolBar):
    """The ``LightBoxToolBar`` is a :class:`.FSLEyesToolBar` for use with the
    :class:`.LightBoxPanel`. A ``LightBoxToolBar`` looks something like this:

    
    .. image:: images/lightboxtoolbar.png
       :scale: 50%
       :align: center

    
    The ``LightBoxToolBar`` allows the user to control important parts of the
    :class:`.LightBoxPanel` display, and also to display a
    :class:`.CanvasSettingsPanel`, which allows control over all aspects of a
    ``LightBoxPanel``.
    """

    
    def __init__(self, parent, overlayList, displayCtx, lb):
        """Create a ``LightBoxToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg lb:          The :class:`.LightBoxPanel` instance.
        """

        fsltoolbar.FSLEyesToolBar.__init__(
            self, parent, overlayList, displayCtx, 24)
        
        self.lightBoxPanel = lb

        lbOpts = lb.getSceneOptions()
        
        icons = {
            'screenshot'       : fslicons.findImageFile('camera24'),
            'movieMode'        : fslicons.findImageFile('movie24'),
            'showMoreSettings' : fslicons.findImageFile('gear24'),

            'zax' : {
                0 : fslicons.findImageFile('sagittalSlice24'),
                1 : fslicons.findImageFile('coronalSlice24'),
                2 : fslicons.findImageFile('axialSlice24'),
            }
        }

        tooltips = {
            
            'screenshot'   : fsltooltips.actions[   lb,      'screenshot'],
            'movieMode'    : fsltooltips.properties[lb,      'movieMode'],
            'zax'          : fsltooltips.properties[lbOpts,  'zax'],
            'sliceSpacing' : fsltooltips.properties[lbOpts,  'sliceSpacing'],
            'zrange'       : fsltooltips.properties[lbOpts,  'zrange'],
            'zoom'         : fsltooltips.properties[lbOpts,  'zoom'],
            'displaySpace' : fsltooltips.properties[displayCtx,
                                                    'displaySpace'],
            
            'showMoreSettings' : fsltooltips.actions[self, 'showMoreSettings'],
        }

        def displaySpaceOptionName(opt):

            if isinstance(opt, fslimage.Image):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt] 
        
        specs = {
            
            'showMoreSettings' : actions.ActionButton(
                'showMoreSettings',
                icon=icons['showMoreSettings'],
                tooltip=tooltips['showMoreSettings']),
            'screenshot' : actions.ActionButton(
                'screenshot',
                icon=icons['screenshot'],
                tooltip=tooltips['screenshot']),

            'movieMode'    : props.Widget(
                'movieMode',
                icon=icons['movieMode'],
                tooltip=tooltips['movieMode']), 
            
            'zax'          : props.Widget(
                'zax',
                icons=icons['zax'],
                tooltip=tooltips['zax']),
            
            'sliceSpacing' : props.Widget(
                'sliceSpacing',
                spin=False,
                showLimits=False,
                tooltip=tooltips['sliceSpacing']),
            
            'zrange'       : props.Widget(
                'zrange',
                spin=False,
                showLimits=False,
                tooltip=tooltips['zrange'],
                labels=[strings.choices[lbOpts, 'zrange', 'min'],
                        strings.choices[lbOpts, 'zrange', 'max']]),
            
            'zoom'         : props.Widget(
                'zoom',
                spin=False,
                showLimits=False,
                tooltip=tooltips['zoom']),
 
            'displaySpace' : props.Widget(
                'displaySpace',
                labels=displaySpaceOptionName,
                tooltip=tooltips['displaySpace'])
        }

        # Slice spacing and zoom go on a single panel
        panel = wx.Panel(self)
        sizer = wx.FlexGridSizer(2, 2)
        panel.SetSizer(sizer)

        more         = props.buildGUI(self,  self, specs['showMoreSettings'])
        screenshot   = props.buildGUI(self,  lb,         specs['screenshot'])
        movieMode    = props.buildGUI(self,  lb,         specs['movieMode'])
        zax          = props.buildGUI(self,  lbOpts,     specs['zax'])
        zrange       = props.buildGUI(self,  lbOpts,     specs['zrange'])
        zoom         = props.buildGUI(panel, lbOpts,     specs['zoom'])
        spacing      = props.buildGUI(panel, lbOpts,     specs['sliceSpacing'])
        displaySpace = props.buildGUI(panel, displayCtx, specs['displaySpace'])
        zoomLabel    = wx.StaticText(panel)
        spacingLabel = wx.StaticText(panel)

        zoomLabel   .SetLabel(strings.properties[lbOpts, 'zoom'])
        spacingLabel.SetLabel(strings.properties[lbOpts, 'sliceSpacing'])

        displaySpace = self.MakeLabelledTool(
            displaySpace,
            strings.properties[displayCtx, 'displaySpace'])

        sizer.Add(zoomLabel)
        sizer.Add(zoom,    flag=wx.EXPAND)
        sizer.Add(spacingLabel)
        sizer.Add(spacing, flag=wx.EXPAND)

        tools = [more, screenshot, zax, movieMode, displaySpace, zrange, panel]
        
        self.SetTools(tools) 


    @actions.toggleAction
    def showMoreSettings(self, *a):
        """Opens a :class:`.CanvasSettingsPanel` for the
        :class:`.LightBoxPanel` that owns this ``LightBoxToolBar``.

        The ``CanvasSettingsPanel`` is opened as a floating pane - see the
        :meth:`.ViewPanel.togglePanel` method.
        """
        import canvassettingspanel
        self.lightBoxPanel.togglePanel(
            canvassettingspanel.CanvasSettingsPanel,
            self.lightBoxPanel,
            floatPane=True) 
