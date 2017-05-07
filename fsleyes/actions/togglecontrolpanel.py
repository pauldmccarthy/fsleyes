#!/usr/bin/env python
#
# togglecontrolpanel.py - The ToggleControlPanelAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ToggleControlPanelAction` class,
an action intended for use by :class:`.ViewPanel` classes to manage
the addition/removal of control panels.
"""


from . import base


class ToggleControlPanelAction(base.ToggleAction):
    """The ``ToggleControlPanelAction`` class is an action which is
    intended to augment :class:`.ViewPanel` actions which add/remove
    a control panel.

    The ``ToggleControlPanelAction`` keeps track of the :class:`.ViewPanel`
    state, and updates its own :attr:`.ToggleAction.toggled` property whenever
    its designated control panel is added/removed from the ``ViewPanel``.

    This sounds a bit silly, but is necessary to ensure that any bound
    widgets (most likely menu items) are updated whenever the control panel
    managed by a ``ToggleControlPanelAction`` is added/removed.
    """

    def __init__(self, func, instance, cpType):
        """Create a ``ToggleControlPanelAction``.

        :arg func:     The function which toggles the
        :arg instance: The :class:`.ViewPanel` instance.
        :arg cpType:   The type of the control panel being managed by this
                       ``ToggleControlPanelAction``.
        """

        import wx.lib.agw.aui as aui

        base.ToggleAction.__init__(self, func, instance)

        self.__viewPanel = instance
        self.__cpType    = cpType

        auiMgr = instance.getAuiManager()

        # WTF. The AuiManager does not post an event
        #      when a pane is added - only when one
        #      is closed. So I have to listen for
        #      whenever the perspective changes. This
        #      includes sash resizes :(
        auiMgr.Bind(aui.EVT_AUI_PERSPECTIVE_CHANGED, self.__viewPanelChanged)


    def __viewPanelChanged(self, ev):
        """Called whenever a control panel is added to/removed from the
        :class:`.ViewPanel` that owns this ``ToggleControlPanelAction``.
        Updates the :attr:`.ToggleAction.toggled` attribute of this action.
        """
        ev.Skip()

        controlPanels = self.__viewPanel.getPanels()
        controlPanels = [type(cp) for cp in controlPanels]

        self.toggled = self.__cpType in controlPanels
