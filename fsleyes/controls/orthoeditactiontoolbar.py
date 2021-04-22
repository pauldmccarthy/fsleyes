#!/usr/bin/env python
#
# orthoeditactiontoolbar.py - Ortho edit mode action toolbar.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoEditActionToolbar`, a toolbar used
by the :class:`.OrthoPanel` in edit mode, which contains various buttons
allowing the user to run various edit-related actions.
"""

import wx

import fsleyes_props                           as props
import fsleyes.controls.controlpanel           as ctrlpanel
import fsleyes.controls.orthoeditsettingspanel as editpanel
import fsleyes.profiles.orthoeditprofile       as orthoeditprofile
import fsleyes.toolbar                         as fsltoolbar
import fsleyes.actions                         as actions
import fsleyes.icons                           as fslicons
import fsleyes.tooltips                        as fsltooltips


class OrthoEditActionToolBar(ctrlpanel.ControlToolBar):
    """The ``OrthoEditActionToolBar`` is a toolbar used by the
    :class:`.OrthoPanel`, which contains buttons allowing the user to:

     - Open the :class:`.OrthoEditSettingsPanel`
     - Create a new :class:`.Image`
     - Undo/redo the last change
     - Clear/fill/erase the current selection
     - Copy/paste data between images
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OrthoEditActionToolBar`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


    @staticmethod
    def profileCls():
        """The ``OrthoEditActionToolBar`` is intended to be activated with the
        :class:`.OrthoEditProfile`.
        """
        return orthoeditprofile.OrthoEditProfile



    @staticmethod
    def ignoreControl():
        """The ``OrthoEditActionToolBar`` is not intended to be explicitly
        added by the user - it is added via :meth:`.OrthoPanel.toggleEditMode`.
        Overriding this method tells the :class:`.FSLeyesFrame` that it
        should not be added to the ortho panel settings menu.
        """
        return True


    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create an ``OrthoEditActionToolBar``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """

        ctrlpanel.ControlToolBar.__init__(self,
                                          parent,
                                          overlayList,
                                          displayCtx,
                                          ortho,
                                          height=24,
                                          orient=wx.VERTICAL,
                                          kbFocus=True)

        self.toggleEditPanel = actions.ToggleControlPanelAction(
            overlayList, displayCtx, ortho, editpanel.OrthoEditSettingsPanel)

        self.__ortho = ortho
        self.__createTools()


    def destroy(self):
        """Must be called when this ``OrthoEditActionToolBar`` is no longer
        needed. Clears references, and calls the base-class ``destroy`` method.
        """
        super().destroy()
        self.__ortho = None


    def __createTools(self):
        """Called when the :attr:`.ViewPanel.profile` property of the
        :class:`.OrthoPanel` changes. Shows/hides edit controls accordingly.
        """

        self.ClearTools(destroy=True, postevent=False)

        ortho      = self.__ortho
        profileObj = ortho.currentProfile

        tools = []
        nav   = []

        for spec in _TOOLBAR_SPECS:

            if spec == 'div':
                tools.append(fsltoolbar.ToolBarDivider(self,
                                                       height=24,
                                                       orient=wx.HORIZONTAL))
                continue

            if spec.key == 'toggleEditPanel': target = self
            else:                             target = profileObj

            widget    = props.buildGUI(self, target, spec)
            navWidget = widget

            if spec.label is not None:
                widget = self.MakeLabelledTool(widget, spec.label)

            tools.append(widget)
            nav  .append(navWidget)

        self.SetTools(tools)
        self.setNavOrder(nav)


_ICONS = {

    'locationFollowsMouse' : [
        fslicons.findImageFile('locationFollowsMouseHighlight24'),
        fslicons.findImageFile('locationFollowsMouse24')],

    'showSelection' : [
        fslicons.findImageFile('showSelectionHighlight24'),
        fslicons.findImageFile('showSelection24')],

    'toggleEditPanel'    : [fslicons.findImageFile('editSpannerHighlight24'),
                            fslicons.findImageFile('editSpanner24')],
    'undo'               : fslicons.findImageFile('undo24'),
    'redo'               : fslicons.findImageFile('redo24'),
    'createMask'         : fslicons.findImageFile('new24'),
    'clearSelection'     : fslicons.findImageFile('clearSelection24'),
    'fillSelection'      : fslicons.findImageFile('fillSelection24'),
    'eraseSelection'     : fslicons.findImageFile('eraseSelection24'),
    'copyPasteData'      : [fslicons.findImageFile('copyDataHighlight24'),
                            fslicons.findImageFile('copyData24')],
    'copyPasteSelection' : [fslicons.findImageFile('copySelectionHighlight24'),
                            fslicons.findImageFile('copySelection24')]

}


_TOOLTIPS = {

    'locationFollowsMouse' : fsltooltips.properties['OrthoEditProfile.'
                                                    'locationFollowsMouse'],
    'showSelection'        : fsltooltips.properties['OrthoEditProfile.'
                                                    'showSelection'],

    'toggleEditPanel'    : fsltooltips.actions['OrthoPanel.'
                                               'toggleEditPanel'],
    'undo'               : fsltooltips.actions['OrthoEditProfile.'
                                               'undo'],
    'redo'               : fsltooltips.actions['OrthoEditProfile.'
                                               'redo'],
    'createMask'         : fsltooltips.actions['OrthoEditProfile.'
                                               'createMask'],
    'clearSelection'     : fsltooltips.actions['OrthoEditProfile.'
                                               'clearSelection'],
    'fillSelection'      : fsltooltips.actions['OrthoEditProfile.'
                                               'fillSelection'],
    'eraseSelection'     : fsltooltips.actions['OrthoEditProfile.'
                                               'eraseSelection'],
    'copyPasteData'      : fsltooltips.actions['OrthoEditProfile.'
                                               'copyPasteData'],
    'copyPasteSelection' : fsltooltips.actions['OrthoEditProfile.'
                                               'copyPasteSelection'],
}

_TOOLBAR_SPECS = [

    actions.ToggleActionButton(
        'toggleEditPanel',
        actionKwargs={'floatPane' : True},
        icon=_ICONS['toggleEditPanel'],
        tooltip=_TOOLTIPS['toggleEditPanel']),
    actions.ActionButton(
        'createMask',
        icon=_ICONS['createMask'],
        tooltip=_TOOLTIPS['createMask']),

    'div',

    props.Widget(
        'locationFollowsMouse',
        icon=_ICONS['locationFollowsMouse'],
        tooltip=_TOOLTIPS['locationFollowsMouse']),

    'div',


    actions.ActionButton(
        'undo',
        icon=_ICONS['undo'],
        tooltip=_TOOLTIPS['undo']),
    actions.ActionButton(
        'redo',
        icon=_ICONS['redo'],
        tooltip=_TOOLTIPS['redo']),

    'div',

    props.Widget(
        'showSelection',
        icon=_ICONS['showSelection'],
        tooltip=_TOOLTIPS['showSelection'],
        dependencies=['drawMode'],
        enabledWhen=lambda i, m: not m),
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

    'div',

    actions.ToggleActionButton(
        'copyPasteData',
        icon=_ICONS['copyPasteData'],
        tooltip=_TOOLTIPS['copyPasteData']),

    actions.ToggleActionButton(
        'copyPasteSelection',
        icon=_ICONS['copyPasteSelection'],
        tooltip=_TOOLTIPS['copyPasteSelection']),
]
