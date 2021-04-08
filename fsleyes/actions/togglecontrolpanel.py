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


import wx.lib.agw.aui as aui

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

    def __init__(self,
                 overlayList,
                 displayCtx,
                 func,
                 viewPanel,
                 cpType,
                 name=None,
                 instance=False):
        """Create a ``ToggleControlPanelAction``.

        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext`
        :arg func:        The function which toggles the control panel
        :arg viewPanel:   The :class:`.ViewPanel` instance.
        :arg cpType:      The type of the control panel being managed by this
                          ``ToggleControlPanelAction``.
        :arg name:        Name of this action - defaults to ``func.__name__``.

        :arg instance:    Defaults to ``False``. If ``True``, it is assumed
                          that this action encapsulates a method of the
                          ``viewPanel`` instance, which will be passed as the
                          first argument when the action is called. This should
                          not need to be used by anything other than the
                          :func:`.toggleControlPanelAction` decorator.
        """

        if instance: instance = viewPanel
        else:        instance = None

        base.ToggleAction.__init__(
            self, overlayList, displayCtx, func, instance=instance, name=name)

        self.__viewPanel = viewPanel
        self.__cpType    = cpType

        auiMgr = viewPanel.auiManager

        # WTF. The AuiManager does not post an event
        #      when a pane is added - only when one
        #      is closed. So I have to listen for
        #      whenever the perspective changes. This
        #      includes sash resizes :(
        auiMgr.Bind(aui.EVT_AUI_PERSPECTIVE_CHANGED, self.__viewPanelChanged)


    @property
    def viewPanel(self):
        """Returns a reference to the :class:`.ViewPanel` that is associated
        with this action.
        """
        return self.__viewPanel


    def destroy(self):
        """Must be called when this ``ToggleControlPanelAction`` is no longer
        used. Clears references, and calls the base-class ``destroy`` method.
        """

        if self.destroyed:
            return

        base.ToggleAction.destroy(self)

        self.__viewPanel.auiManager.Unbind(aui.EVT_AUI_PERSPECTIVE_CHANGED)
        self.__viewPanel = None


    def __viewPanelChanged(self, ev):
        """Called whenever a control panel is added to/removed from the
        :class:`.ViewPanel` that owns this ``ToggleControlPanelAction``.
        Updates the :attr:`.ToggleAction.toggled` attribute of this action.
        """
        ev.Skip()

        controlPanels = self.__viewPanel.getPanels()
        controlPanels = [type(cp) for cp in controlPanels]

        self.toggled = self.__cpType in controlPanels
