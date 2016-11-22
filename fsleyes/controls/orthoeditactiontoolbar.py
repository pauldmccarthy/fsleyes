#!/usr/bin/env python
#
# orthoeditpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import wx

import props

import fsleyes.actions     as actions
import fsleyes.icons       as fslicons
import fsleyes.toolbar     as fsltoolbar
import fsleyes.tooltips    as fsltooltips


class OrthoEditActionToolBar(fsltoolbar.FSLeyesToolBar):

    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """Create an ``OrthoEditActionToolBar``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        
        fsltoolbar.FSLeyesToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           frame,
                                           height=24,
                                           orient=wx.VERTICAL,
                                           kbFocus=True) 

        self.__ortho = ortho

        ortho.addListener('profile', self._name, self.__profileChanged)

        self.__profileChanged()


    def destroy(self):
        """Must be called when this ``OrthoEditAction`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.FSLeyesToolBar.destroy` method.
        """
        self.__ortho.removeListener('profile', self._name)
        fsltoolbar.FSLeyesToolBar.destroy(self)


    def __profileChanged(self, *a):
        """Called when the :attr:`.ViewPanel.profile` property of the
        :class:`.OrthoPanel` changes. Shows/hides edit controls accordingly.
        """

        self.ClearTools(destroy=True, postevent=False)
        
        ortho      = self.__ortho
        profile    = ortho.profile
        profileObj = ortho.getCurrentProfile()
        
        if profile != 'edit':
            return
                
        tools = []
        nav   = []

        for spec in _TOOLBAR_SPECS:

            target    = profileObj
            widget    = props.buildGUI(self, target, spec)
            navWidget = widget

            if spec.label is not None:
                widget = self.MakeLabelledTool(widget, spec.label)
                
            tools.append(widget)
            nav  .append(navWidget)

        self.SetTools(tools)
        self.setNavOrder(nav)


_ICONS = {

    'clearSelection'          :  fslicons.findImageFile('clear24'),
    'undo'                    :  fslicons.findImageFile('undo24'),
    'redo'                    :  fslicons.findImageFile('redo24'),
    'fillSelection'           :  fslicons.findImageFile('fill24'),
    'eraseSelection'          :  fslicons.findImageFile('eraseSelection24'),
    'createMaskFromSelection' :  fslicons.findImageFile('createMask24'),
    'createROIFromSelection'  :  fslicons.findImageFile('createROI24'),

}
        

_TOOLTIPS = {

    'clearSelection'          : fsltooltips.actions['OrthoEditProfile.'
                                                    'clearSelection'],
    'eraseSelection'          : fsltooltips.actions['OrthoEditProfile.'
                                                    'eraseSelection'], 
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

}
        
_TOOLBAR_SPECS = [

    actions.ActionButton(
        'undo',
        icon=_ICONS['undo'],
        tooltip=_TOOLTIPS['undo']),
    actions.ActionButton(
        'redo',
        icon=_ICONS['redo'],
        tooltip=_TOOLTIPS['redo']),
    actions.ActionButton(
        'clearSelection',
        icon=_ICONS['clearSelection'],
        tooltip=_TOOLTIPS['clearSelection']),
    actions.ActionButton(
        'fillSelection',
        icon=_ICONS['fillSelection'],
        tooltip=_TOOLTIPS['fillSelection']),
    actions.ActionButton(
        'eraseSelection',
        icon=_ICONS['eraseSelection'],
        tooltip=_TOOLTIPS['eraseSelection']), 
    actions.ActionButton(
        'createMaskFromSelection',
        icon=_ICONS['createMaskFromSelection'],
        tooltip=_TOOLTIPS['createMaskFromSelection']),
    actions.ActionButton(
        'createROIFromSelection',
        icon=_ICONS['createROIFromSelection'],
        tooltip=_TOOLTIPS['createROIFromSelection']),
]
