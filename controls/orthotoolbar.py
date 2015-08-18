#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import props

import fsl.fsleyes.toolbar as fsltoolbar
import fsl.fsleyes.icons   as icons
import fsl.fsleyes.actions as actions
import fsl.data.strings    as strings


class OrthoToolBar(fsltoolbar.FSLEyesToolBar):

    
    def __init__(self, parent, overlayList, displayCtx, ortho):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLEyesToolBar.__init__(
            self, parent, overlayList, displayCtx, 24, actionz)
        
        self.orthoPanel = ortho

        # The toolbar has buttons bound to some actions
        # on the Profile  instance - when the profile
        # changes (between 'view' and 'edit'), the
        # Profile instance changes too, so we need
        # to re-create these action buttons. I'm being
        # lazy and just re-generating the entire toolbar.
        ortho.addListener('profile', self._name, self.__makeTools)

        self.__makeTools()


    def __makeTools(self, *a):
        
        ortho     = self.orthoPanel
        orthoOpts = ortho.getSceneOptions()
        profile   = ortho.getCurrentProfile()

        icns = {
            'screenshot'  : icons.findImageFile('camera24'),
            'showXCanvas' : icons.findImageFile('sagittalSlice24'),
            'showYCanvas' : icons.findImageFile('coronalSlice24'),
            'showZCanvas' : icons.findImageFile('axialSlice24'),
            'more'        : icons.findImageFile('gear24'),

            'resetZoom'    : icons.findImageFile('resetZoom24'),
            'centreCursor' : icons.findImageFile('centre24'),

            'layout' : {
                'horizontal' : icons.findImageFile('horizontalLayout24'),
                'vertical'   : icons.findImageFile('verticalLayout24'),
                'grid'       : icons.findImageFile('gridLayout24'),
            }
        }

        toolSpecs = [

            actions.ActionButton('more',         icon=icns['more']),
            actions.ActionButton('screenshot',   icon=icns['screenshot']),
            props  .Widget(      'showXCanvas',  icon=icns['showXCanvas']),
            props  .Widget(      'showYCanvas',  icon=icns['showYCanvas']),
            props  .Widget(      'showZCanvas',  icon=icns['showZCanvas']),
            props  .Widget(      'layout',       icons=icns['layout']),
            actions.ActionButton('resetZoom',    icon=icns['resetZoom']),
            actions.ActionButton('centreCursor', icon=icns['centreCursor']),
            
            props.Widget('zoom', spin=False, showLimits=False),
        ]
        
        targets    = {'screenshot'   : ortho,
                      'zoom'         : orthoOpts,
                      'layout'       : orthoOpts,
                      'showXCanvas'  : orthoOpts,
                      'showYCanvas'  : orthoOpts,
                      'showZCanvas'  : orthoOpts,
                      'resetZoom'    : profile,
                      'centreCursor' : profile,
                      'more'         : self}

        tools = []
        
        for spec in toolSpecs:
            widget = props.buildGUI(self, targets[spec.key], spec)

            if spec.key == 'zoom':
                widget = self.MakeLabelledTool(
                    widget,
                    strings.properties[targets[spec.key], 'zoom'])
            
            tools.append(widget)

        self.SetTools(tools, destroy=True) 

    
    def showMoreSettings(self, *a):
        import canvassettingspanel
        self.orthoPanel.togglePanel(canvassettingspanel.CanvasSettingsPanel,
                                    self.orthoPanel,
                                    floatPane=True)
