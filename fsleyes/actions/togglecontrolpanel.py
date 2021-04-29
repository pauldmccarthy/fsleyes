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
                 viewPanel,
                 cpType,
                 func=None,
                 name=None,
                 **kwargs):
        """Create a ``ToggleControlPanelAction``.

        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext`
        :arg viewPanel:   The :class:`.ViewPanel` instance.
        :arg cpType:      The type of the control panel being managed by this
                          ``ToggleControlPanelAction``.
        :arg func:        The function which toggles the control panel. If
                          not provided, a default function is used.
        :arg name:        Name of this action - defaults to ``func.__name__``.

        All other arguments will be passed to the
        :meth:`.ViewPanel.togglePanel` method.
        """

        if func is None:
            func = self.__togglePanel

        base.ToggleAction.__init__(
            self, overlayList, displayCtx, func, name=name)

        self.__viewPanel = viewPanel
        self.__cpType    = cpType
        self.__kwargs    = kwargs

        # Listen for changes to the view panel layout
        # so we can detect when the user closes our
        # control panel. The granularity of AuiManager
        # event notifications is somewhat coarse, so
        # this callback will be called whenever the
        # perspective changes. This includes sash
        # resizes :(
        viewPanel.events.register(self.name,
                                  self.__viewPanelChanged,
                                  topic='aui_perspective')


    def __togglePanel(self, *args, **kwargs):
        """Default action to run if a ``func`` wasn't specified. Calls
        :class:`.ViewPanel.togglePanel`,
        """
        self.viewPanel.togglePanel(self.__cpType,
                                   *args,
                                   **kwargs,
                                   **self.__kwargs)


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

        if not self.__viewPanel.destroyed:
            self.__viewPanel.events.deregister(
                self.name, topic='aui_perspective')
        self.__viewPanel = None

        base.ToggleAction.destroy(self)


    def __viewPanelChanged(self, *a):
        """Called whenever a control panel is added to/removed from the
        :class:`.ViewPanel` that owns this ``ToggleControlPanelAction``.
        Updates the :attr:`.ToggleAction.toggled` attribute of this action.
        """

        if self.destroyed:
            return

        controlPanels = self.__viewPanel.getPanels()
        controlPanels = [type(cp) for cp in controlPanels]
        self.toggled = self.__cpType in controlPanels
