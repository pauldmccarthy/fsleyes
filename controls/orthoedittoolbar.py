#!/usr/bin/env python
#
# orthoedittoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import props

import fsl.fsleyes.toolbar  as fsltoolbar
import fsl.fsleyes.actions  as actions
import fsl.fsleyes.icons    as fslicons
import fsl.fsleyes.tooltips as fsltooltips
import fsl.data.strings     as strings

from fsl.fsleyes.profiles.orthoeditprofile import OrthoEditProfile


log = logging.getLogger(__name__)

# Some of the toolbar widgets are labelled 
_LABELS = {

    'selectionCursorColour'  : strings.properties[OrthoEditProfile,
                                                  'selectionCursorColour'],
    'selectionOverlayColour' : strings.properties[OrthoEditProfile,
                                                  'selectionOverlayColour'],
    'selectionSize'          : strings.properties[OrthoEditProfile,
                                                  'selectionSize'],
    'intensityThres'         : strings.properties[OrthoEditProfile,
                                                  'intensityThres'],
    'searchRadius'           : strings.properties[OrthoEditProfile,
                                                  'searchRadius'],
    'fillValue'              : strings.properties[OrthoEditProfile,
                                                  'fillValue'], 
}

_ICONS = {
    'view'                    : fslicons.findImageFile('eye24'),
    'edit'                    : fslicons.findImageFile('pencil24'),
    'selectionIs3D'           : [fslicons.findImageFile('selection3D24'),
                                 fslicons.findImageFile('selection2D24')],
    'clearSelection'          : fslicons.findImageFile('clear24'),
    'undo'                    : fslicons.findImageFile('undo24'),
    'redo'                    : fslicons.findImageFile('redo24'),
    'fillSelection'           : fslicons.findImageFile('fill24'),
    'createMaskFromSelection' : fslicons.findImageFile('createMask24'),
    'createROIFromSelection'  : fslicons.findImageFile('createROI24'),
    'limitToRadius'           : fslicons.findImageFile('radius24'),
    'localFill'               : fslicons.findImageFile('localsearch24'),
    'selint'                  : fslicons.findImageFile('selectByIntensity24'),
}

_TOOLTIPS = {
    'profile'                 : fsltooltips.properties['OrthoPanel.profile'],
    'selectionIs3D'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'selectionIs3D'],
    
    'clearSelection'          : fsltooltips.actions['OrthoEditProfile.'
                                                    'clearSelection'],
    'undo'                    : fsltooltips.actions['OrthoEditProfile.'
                                                    'undo'],
    'redo'                    : fsltooltips.actions['OrthoEditProfile.'
                                                    'redo'],
    'fillSelection'           : fsltooltips.actions['OrthoEditProfile.'
                                                    'fillSelection'],
    'createMaskFromSelection' : fsltooltips.actions['OrthoEditProfile.'
                                                    'createMaskFromSelection'],
    'createROIFromSelection'  : fsltooltips.actions['OrthoEditProfile.'
                                                    'createROIFromSelection'],
    
    'selint'                  : fsltooltips.properties['OrthoEditToolBar.'
                                                       'selint'],
    'limitToRadius'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'limitToRadius'],
    'searchRadius'            : fsltooltips.properties['OrthoEditProfile.'
                                                       'searchRadius'],
    'localFill'               : fsltooltips.properties['OrthoEditProfile.'
                                                       'localFill'],
    'selectionCursorColour'   : fsltooltips.properties['OrthoEditProfile.sel'
                                                       'ectionCursorColour'],
    'selectionOverlayColour'  : fsltooltips.properties['OrthoEditProfile.sel'
                                                       'ectionOverlayColour'],
    'selectionSize'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'selectionSize'],
    'fillValue'               : fsltooltips.properties['OrthoEditProfile.'
                                                       'fillValue'],
    'intensityThres'          : fsltooltips.properties['OrthoEditProfile.'
                                                       'intensityThres'],
}

_TOOLBAR_SPECS  = {

    'profile' : props.Widget(
        'profile',
        tooltip=_TOOLTIPS['profile'],
        icons={
            'view' : _ICONS['view'],
            'edit' : _ICONS['edit']}),

    'view' : {},

    'edit' : [
        props.Widget(
            'selectionIs3D',
            enabledWhen=lambda p: p.mode in ['sel', 'desel'],
            icon=_ICONS['selectionIs3D'],
            tooltip=_TOOLTIPS['selectionIs3D'],
            toggle=True),
        actions.ActionButton(
            'clearSelection',
            icon=_ICONS['clearSelection'],
            tooltip=_TOOLTIPS['clearSelection']),
        actions.ActionButton(
            'undo',
            icon=_ICONS['undo'],
            tooltip=_TOOLTIPS['undo']),
        actions.ActionButton(
            'redo',
            icon=_ICONS['redo'],
            tooltip=_TOOLTIPS['redo']),
        actions.ActionButton(
            'fillSelection',
            icon=_ICONS['fillSelection'],
            tooltip=_TOOLTIPS['fillSelection']),
        actions.ActionButton(
            'createMaskFromSelection',
            icon=_ICONS['createMaskFromSelection'],
            tooltip=_TOOLTIPS['createMaskFromSelection']),
        actions.ActionButton(
            'createROIFromSelection',
            icon=_ICONS['createROIFromSelection'],
            tooltip=_TOOLTIPS['createROIFromSelection']),
        props.Widget(
            'selint',
            icon=_ICONS['selint'],
            tooltip=_TOOLTIPS['selint']),
        props.Widget(
            'limitToRadius',
            icon=_ICONS['limitToRadius'],
            tooltip=_TOOLTIPS['limitToRadius'],
            enabledWhen=lambda p: p.mode == 'selint'),
        props.Widget(
            'localFill',
            icon=_ICONS['localFill'],
            tooltip=_TOOLTIPS['localFill'],
            enabledWhen=lambda p: p.mode == 'selint'),
        props.Widget(
            'selectionCursorColour',
            label=_LABELS['selectionCursorColour'],
            tooltip=_TOOLTIPS['selectionCursorColour']),
        props.Widget(
            'selectionOverlayColour',
            label=_LABELS['selectionOverlayColour'],
            tooltip=_TOOLTIPS['selectionOverlayColour']), 
        props.Widget(
            'selectionSize',
            enabledWhen=lambda p: p.mode in ['sel', 'desel'],
            label=_LABELS['selectionSize'],
            tooltip=_TOOLTIPS['selectionSize']),
        props.Widget(
            'fillValue',
            label=_LABELS['fillValue'],
            tooltip=_TOOLTIPS['fillValue']),
        props.Widget(
            'intensityThres',
            label=_LABELS['intensityThres'],
            tooltip=_TOOLTIPS['intensityThres'],
            enabledWhen=lambda p: p.mode == 'selint'),

        props.Widget(
            'searchRadius',
            label=_LABELS['searchRadius'],
            tooltip=_TOOLTIPS['searchRadius'],
            enabledWhen=lambda p: p.mode == 'selint' and p.limitToRadius)
    ]
}



class OrthoEditToolBar(fsltoolbar.FSLEyesToolBar):

    
    selint = props.Boolean(default=False)


    def __init__(self, parent, overlayList, displayCtx, ortho):
        fsltoolbar.FSLEyesToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           24)

        self.orthoPanel = ortho

        self .addListener('selint',  self._name, self.__selintChanged)
        ortho.addListener('profile', self._name, self.__profileChanged)

        self.__profileTool = props.buildGUI(
            self,
            ortho,
            _TOOLBAR_SPECS['profile'])

        self.AddTool(self.__profileTool)

        self.__profileChanged()


    def destroy(self):
        self.orthoPanel.removeListener('profile', self._name)
        fsltoolbar.FSLEyesToolBar.destroy(self)


    def __selintChanged(self, *a):

        ortho = self.orthoPanel

        if ortho.profile != 'edit':
            return
        
        profile = ortho.getCurrentProfile()
        
        if self.selint: profile.mode = 'selint'
        else:           profile.mode = 'sel'


    def __profileChanged(self, *a):

        # We don't want to remove the profile tool
        # created in __init__, so we skip the first
        # tool
        self.ClearTools(startIdx=1, destroy=True, postevent=False)
                
        ortho      = self.orthoPanel
        profile    = ortho.profile
        profileObj = ortho.getCurrentProfile()

        if profile == 'edit':
            self.disableNotification('selint')
            self.selint = profileObj.mode == 'selint'
            self.enableNotification('selint')

        specs = _TOOLBAR_SPECS[profile]

        tools = []

        for spec in specs:

            if spec.key == 'selint': target = self
            else:                    target = profileObj
            
            widget = props.buildGUI(self, target, spec)
            if spec.label is not None:
                widget = self.MakeLabelledTool(widget, spec.label)
                
            tools.append(widget)

        self.InsertTools(tools, 1)
