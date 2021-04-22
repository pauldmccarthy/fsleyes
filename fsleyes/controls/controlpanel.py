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

import fsl.utils.deprecated       as deprecated
import fsleyes_widgets.widgetlist as widgetlist
import fsleyes.panel              as fslpanel
import fsleyes.toolbar            as fsltoolbar


class ControlMixin:
    """Mixin class for the :class:`ControlPanel` and :class:`ControlToolBar`.
    """

    @staticmethod
    def title():
        """May be overridden by sub-classes. Returns a title to be used
        in menus and window title bars.
        """
        return None


    @staticmethod
    def ignoreControl():
        """Tell FSLeyes that this control should not be considered a FSLeyes
        plugin.

        The default implementation returns ``False``, but may be overridden
        by sub-classes to control whether a menu item should be added for
        the control in the settings menu for the relevant FSLeyes view(s).

        Note that this method must be implemented on the class that is to
        be ignored - inherited implementations from base classes are not
        considered.
        """
        return False


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
    def supportSubClasses():
        """May be overridden by sub-classes. If this control panel is intended
        for use with specific views, via the :meth:`supportedViews` method,
        this method specifies whether sub-classes of the :meth:`supportedViews`
        are supported (the default), or whether only the specific classes in
        :meth:`supportedViews` are supported.

        Note that this method must be implemented on the specific control
        class that wishes to use it - it is not considered if implemented in a
        base classe.
        """
        return True


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


    @staticmethod
    def profileCls():
        """Return the custom interaction profile associated with this control.
        Must be a sub-class of :class:`.Profile`.

        When a control panel is opened, if it requires a different profile to
        the one that is active, that profile is created and activated. If any
        other controls required the previous profile, they are closed.

        Control panels which are associated with an interaction profile can
        assume that the profile has already been created by the time the
        control is created. The :class:`.Profile` instance can be retrieved
        via :meth:`.ViewPanel.currentProfile`.
        """
        return None


class ControlPanel(fslpanel.FSLeyesPanel, ControlMixin):
    """The ``ControlPanel`` is the base class for all FSLeyes controls.
    All sub-classes must call ``__init__``.
    """


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 viewPanel,
                 *args,
                 **kwargs):
        """Create a ``ControlPanel``.

        :arg parent:      Parent ``wx`` object
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` associated with
                          ``viewPanel``.
        :arg viewPanel:   The FSLeyes :class:`.ViewPanel` that owns this
                          ``ControlPanel``

        All other arguments are passed through to the ``FSLeyesPanel``.
        """

        # Prior to FSLeyes 1.0.0, the fourth argument
        # was the FSLeyesFrame. This clause is in place
        # to retain support for third-party FSLeyes
        # plugins which were written before 1.0.0
        import fsleyes.frame as fslframe
        if isinstance(viewPanel, fslframe.FSLeyesFrame):
            frame     = viewPanel
            viewPanel = None
            deprecated.warn(
                type(self).__name__, '1.0.0', '2.0.0',
                'You should pass the view panel, not the FSLeyesFrame')
        else:
            frame = viewPanel.frame

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame, *args, **kwargs)
        self.__viewPanel = viewPanel


    def destroy(self):
        """Must be called when this ``ControlPanel`` is no longer needed.
        Clears references and calls the base class ``destroy`` method.
        """
        fslpanel.FSLeyesPanel.destroy(self)
        self.__viewPanel = None


    @property
    def viewPanel(self):
        """Returns a reference to the :class:`.ViewPanel` that owns this
        :class:`.ControlPanel`.
        """
        return self.__viewPanel


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

        self.__widgets = widgetlist.WidgetList(self, minHeight=24)
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
