#!/usr/bin/env python
#
# controlpanel.py - The ControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ControlPanel`, :class:`ControlToolBar`,
and :class:`SettingsPanel` classes, base-classes for all FSLeyes controls.

See the :mod:`fsleyes` package documentation for an overview of FSLeyes views
and controls.

The :class:`SettingsPanel` is a convenience
class for certain *FSLeyes* control panels (see the ::mod:`fsleyes`
documentation).
"""


import                   wx
import wx.lib.agw.aui as wxaui

import fsleyes_widgets.widgetlist as widgetlist

import fsleyes.panel              as fslpanel
import fsleyes.toolbar            as fsltoolbar


class ControlMixin(object):
    """Mixin class for the :class:`ControlPanel` and :class:`ControlToolBar`.
    """

    @staticmethod
    def supportedViews():
        """Return the views that this control supports.

        This method may be overridden by sub-classes to return a list of
        the view types that are supported by this control. For example, the
        :class:`.OrthoToolBar` control is intended to be used solely with the
        :class:`.OrthoPanel` view.

        The default implementation returns ``None``, which is interpreted
        as being compatible with all views.
        """
        return None


    @staticmethod
    def defaultLayout():
        """Return default options for :meth:`.ViewPanel.togglePanel`.

        This method may be overridden by sub-classes to return a ``dict``
        containing keyword arguments to be used by the
        :meth:`.ViewPanel.togglePanel` method when a control panel of this
        type is added. When ``togglePanel`` is called, if any arguments are
        provided, the arguments returned by this method are not used.
        """
        return None


class ControlPanel(fslpanel.FSLeyesPanel, ControlMixin):
    """The ``ControlPanel`` is the base class for all FSLeyes controls. """
    pass


class ControlToolBar(fsltoolbar.FSLeyesToolBar, ControlMixin):
    """The ``ControlToolBar`` is the base class for all FSLeyes toolbars. """
    pass


class SettingsPanel(ControlPanel):
    """The ``SettingsPanel`` is a convenience class for *FSLeyes* control
    panels which use a :class:`fsleyes_widgets.WidgetList` to display a
    collection of controls for the user.  When displayed as a dialog/
    floating frame, the ``SettingsPanel`` will automatically resize itself
    to fit its contents. See the :class:`.CanvasSettingsPanel` for an example.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``SettingsPanel``.  All arguments are passed to
        the :meth:`FSLeyesPanel.__init__` method.
        """

        ControlPanel.__init__(self, *args, **kwargs)

        self.__widgets = widgetlist.WidgetList(self)
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        self.SetMinSize((300, 80))

        self.__widgets.Bind(widgetlist.EVT_WL_CHANGE_EVENT,
                            self.__widgetListChange)


    def getWidgetList(self):
        """Returns the :class:`fsleyes_widgets.WidgetList` which should be used
        by sub-classes to display content to the user.
        """
        return self.__widgets


    def __widgetListChange(self, ev):
        """Called whenever the widget list contents change. If this panel
        is floating, its parent is autmatically resized.
        """
        if isinstance(self.GetTopLevelParent(), wxaui.AuiFloatingFrame):
            self.SetInitialSize(self.__widgets.GetBestSize())
            self.GetTopLevelParent().Fit()
