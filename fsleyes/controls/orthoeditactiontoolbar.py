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

import fsleyes_props                 as props

import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.toolbar               as fsltoolbar
import fsleyes.actions               as actions
import fsleyes.icons                 as fslicons
import fsleyes.tooltips              as fsltooltips


class OrthoEditActionToolBar(ctrlpanel.ControlToolBar):
    """The ``OrthoEditActionToolBar`` is a toolbar used by the
    :class:`.OrthoPanel`, which contains buttons allowing the user to:

     - Open the :class:`.OrthoEditSettingsPanel`
     - Create a new :class:`.Image`
     - Undo/redo the last change
     - Clear/fill/erase the current selection
    """

    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """Create an ``OrthoEditActionToolBar``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """

        ctrlpanel.ControlToolBar.__init__(self,
                                          parent,
                                          overlayList,
                                          displayCtx,
                                          frame,
                                          height=24,
                                          orient=wx.VERTICAL,
                                          kbFocus=True)

        self.__ortho = ortho

        ortho.addListener('profile', self.name, self.__profileChanged)

        self.__profileChanged()


    def destroy(self):
        """Must be called when this ``OrthoEditAction`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.ControlToolBar.destroy` method.
        """
        self.__ortho.removeListener('profile', self.name)
        ctrlpanel.ControlToolBar.destroy(self)


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OrthoEditActionToolBar`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


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

            if spec == 'div':
                tools.append(fsltoolbar.ToolBarDivider(self,
                                                       height=24,
                                                       orient=wx.HORIZONTAL))
                continue

            if spec.key == 'toggleEditPanel': target = ortho
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

    'toggleEditPanel' : [fslicons.findImageFile('editSpannerHighlight24'),
                         fslicons.findImageFile('editSpanner24')],
    'undo'            : fslicons.findImageFile('undo24'),
    'redo'            : fslicons.findImageFile('redo24'),
    'createMask'      : fslicons.findImageFile('new24'),
    'clearSelection'  : fslicons.findImageFile('clearSelection24'),
    'fillSelection'   : fslicons.findImageFile('fillSelection24'),
    'eraseSelection'  : fslicons.findImageFile('eraseSelection24'),
    'copySelection'   : fslicons.findImageFile('copySelection24'),
    'pasteSelection'  : fslicons.findImageFile('pasteSelection24'),
}


_TOOLTIPS = {

    'locationFollowsMouse' : fsltooltips.properties['OrthoEditProfile.'
                                                    'locationFollowsMouse'],
    'showSelection'        : fsltooltips.properties['OrthoEditProfile.'
                                                    'showSelection'],

    'toggleEditPanel' : fsltooltips.actions['OrthoPanel.'
                                            'toggleEditPanel'],
    'undo'            : fsltooltips.actions['OrthoEditProfile.'
                                            'undo'],
    'redo'            : fsltooltips.actions['OrthoEditProfile.'
                                            'redo'],
    'createMask'      : fsltooltips.actions['OrthoEditProfile.'
                                            'createMask'],
    'clearSelection'  : fsltooltips.actions['OrthoEditProfile.'
                                            'clearSelection'],
    'fillSelection'   : fsltooltips.actions['OrthoEditProfile.'
                                            'fillSelection'],
    'eraseSelection'  : fsltooltips.actions['OrthoEditProfile.'
                                            'eraseSelection'],
    'copySelection'   : fsltooltips.actions['OrthoEditProfile.'
                                            'copySelection'],
    'pasteSelection'  : fsltooltips.actions['OrthoEditProfile.'
                                            'pasteSelection'],
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

    actions.ActionButton(
        'copySelection',
        icon=_ICONS['copySelection'],
        tooltip=_TOOLTIPS['copySelection']),
    actions.ActionButton(
        'pasteSelection',
        icon=_ICONS['pasteSelection'],
        tooltip=_TOOLTIPS['pasteSelection']),
]
