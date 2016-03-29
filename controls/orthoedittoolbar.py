#!/usr/bin/env python
#
# orthoedittoolbar.py - The OrthoEditToolBar
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoEditToolBar`, a
:class:`.FSLEyesToolBar` which displays controls for editing :class:`.Image`
instances in an :class:`.OrthoPanel`.
"""


import logging

import props

import fsl.fsleyes.toolbar  as fsltoolbar
import fsl.fsleyes.actions  as actions
import fsl.fsleyes.icons    as fslicons
import fsl.fsleyes.tooltips as fsltooltips
import fsl.fsleyes.strings  as strings

from fsl.fsleyes.profiles.orthoeditprofile import OrthoEditProfile


log = logging.getLogger(__name__)


class OrthoEditToolBar(fsltoolbar.FSLEyesToolBar):
    """The ``OrthoEditToolBar`` is a :class:`.FSLEyesToolBar` which displays
    controls for editing :class:`.Image` instances in an :class:`.OrthoPanel`.

    An ``OrthoEditToolBar`` looks something like this:

    
    .. image:: images/orthoedittoolbar.png
       :scale: 50%
       :align: center

    
    The ``OrthoEditToolBar`` exposes properties and actions which are defined
    on the :class:`.OrthoEditProfile` class, and allows the user to:

     - Change the :class:`.OrthoPanel` profile  between ``view`` and ``edit``
       mode (see the :attr:`.ViewPanel.profile` property). When in ``view``
       mode, all of the other controls are hidden.

     - Undo/redo changes to the selection and to :class:`.Image` instances.

     - Clear and fill the current selection.

     - Switch between a 2D and 3D selection cursor.

     - Change the selection cursor size.

     - Create a new mask/ROI :class:`.Image` from the current selection.

     - Switch between regular *select* mode, and *select by intensity* mode,
       and adjust the select by intensity mode settings.

    
    All of the controls shown on an ``OrthoEditToolBar`` instance are defined
    in the :attr:`_TOOLBAR_SPECS` dictionary.
    """

    
    selint = props.Boolean(default=False)
    """This property allows the user to change the :class:`.OrthoEditProfile`
    between ``sel`` mode, and ``selint`` mode.
    """


    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create an ``OrthoEditToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        fsltoolbar.FSLEyesToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           24)

        self.__orthoPanel = ortho

        self .addListener('selint',  self._name, self.__selintChanged)
        ortho.addListener('profile', self._name, self.__profileChanged)

        self.__profileTool = props.buildGUI(
            self,
            ortho,
            _TOOLBAR_SPECS['profile'])

        self.AddTool(self.__profileTool)

        self.__profileChanged()


    def destroy(self):
        """Must be called when this ``OrthoEditToolBar`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.FSLEyesToolBar.destroy` method.
        """
        self.__orthoPanel.removeListener('profile', self._name)
        fsltoolbar.FSLEyesToolBar.destroy(self)


    def __selintChanged(self, *a):
        """Called when the :attr:`selint` property changes. If the
        :class:`OrthoPanel` is currently in ``edit`` mode, toggles the
        associated :class:`.OrthoEditProfile` instance between ``sel``
        and ``selint`` modes.
        """

        ortho = self.__orthoPanel

        if ortho.profile != 'edit':
            return
        
        profile = ortho.getCurrentProfile()
        
        if self.selint: profile.mode = 'selint'
        else:           profile.mode = 'nav'


    def __profileChanged(self, *a):
        """Called when the :attr:`.ViewPanel.profile` property of the
        :class:`.OrthoPanel` changes. Shows/hides edit controls accordingly.
        """

        # We don't want to remove the profile tool
        # created in __init__, so we skip the first
        # tool
        self.ClearTools(startIdx=1, destroy=True, postevent=False)
                
        ortho      = self.__orthoPanel
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
"""This dictionary contains labels for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


_ICONS = {
    'view'                    :  [
        fslicons.findImageFile('eyeHighlight24'),
        fslicons.findImageFile('eye24')],
    'edit'                    :  [
        fslicons.findImageFile('pencilHighlight24'),
        fslicons.findImageFile('pencil24')],
    'selectionIs3D'           : [
        fslicons.findImageFile('selection3DHighlight24'),
        fslicons.findImageFile('selection3D24'),
        fslicons.findImageFile('selection2DHighlight24'),
        fslicons.findImageFile('selection2D24')],
    
    'clearSelection'          :  fslicons.findImageFile('clear24'),
    'undo'                    :  fslicons.findImageFile('undo24'),
    'redo'                    :  fslicons.findImageFile('redo24'),
    'fillSelection'           :  fslicons.findImageFile('fill24'),
    'eraseSelection'          :  fslicons.findImageFile('erase24'),
    'createMaskFromSelection' :  fslicons.findImageFile('createMask24'),
    'createROIFromSelection'  :  fslicons.findImageFile('createROI24'),
    
    'limitToRadius'           :  [
        fslicons.findImageFile('radiusHighlight24'),
        fslicons.findImageFile('radius24')],
    'localFill'               :  [
        fslicons.findImageFile('localsearchHighlight24'),
        fslicons.findImageFile('localsearch24')],
    'selint'                  :  [
        fslicons.findImageFile('selectByIntensityHighlight24'),
        fslicons.findImageFile('selectByIntensity24')],
}
"""This dictionary contains icons for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


_TOOLTIPS = {
    'profile'                 : fsltooltips.properties['OrthoPanel.profile'],
    'selectionIs3D'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'selectionIs3D'],
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
"""This dictionary contains tooltips for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


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
            icon=_ICONS['selectionIs3D'],
            tooltip=_TOOLTIPS['selectionIs3D'],
            toggle=False),
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
            label=_LABELS['selectionSize'],
            tooltip=_TOOLTIPS['selectionSize']),
        props.Widget(
            'fillValue',
            label=_LABELS['fillValue'],
            tooltip=_TOOLTIPS['fillValue'],
            slider=False),
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
"""This dictionary contains specifications for all of the tools shown in an
:class:`OrthoEditToolBar`. The following keys are defined:

  =========== ===========================================================
  ``profile`` Contains a single specification defining the control for
              switching the :class:`.OrthoPanel` between ``view`` and
              ``edit`` profiles.
  ``view``    A list of specifications defining controls to be shown when
              the ``view`` profile is active.
  ``edit``    A list of specifications defining controls to be shown when
              the ``view`` profile is active.
  =========== ===========================================================
"""
