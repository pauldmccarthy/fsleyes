#!/usr/bin/env python


import                                  wx
import wx.lib.agw.aui                as aui
import wx.lib.agw.aui.framemanager   as auifm
import fsleyes_widgets               as fwidgets
import fsleyes.controls.controlpanel as ctrlpanel


class MyAuiFloatingFrame(auifm.AuiFloatingFrame):
    """Here I am monkey patching the
    ``wx.agw.aui.framemanager.AuiFloatingFrame.__init__`` method.

    I am doing this because I have observed some strange behaviour when running
    a remote instance of this application over an SSH/X11 session, with the X11
    server (i.e. the local machine) running in OS X. When a combobox is embedded
    in a floating frame (either a pane or a toolbar), its dropdown list appears
    underneath the frame, meaning that the user is unable to actually select any
    items from the list!

    I have only seen this behaviour when using XQuartz on macOS.

    Ultimately, this appears to be caused by the ``wx.FRAME_TOOL_WINDOW``
    style, as passed to the ``wx.MiniFrame`` constructor (from which the
    ``AuiFloatingFrame`` class derives). Removing this style flag fixes the
    problem, so this is exactly what I'm doing. I haven't looked any deeper
    into the situation.


    This class also overrieds the ``SetPaneWindow`` method, because under gtk3,
    the maximum size if a frame musr be set.
    """

    def __init__(self, *args, **kwargs):
        """My new constructor, which makes sure that the ``FRAME_TOOL_WINDOW``
        style is not passed through to the ``AuiFloatingFrame`` constructor
        """

        if 'style' in kwargs:
            style = kwargs['style']

        # This is the default style, as defined
        # in the AuiFloatingFrame constructor
        else:
            style = (wx.FRAME_TOOL_WINDOW     |
                     wx.FRAME_FLOAT_ON_PARENT |
                     wx.FRAME_NO_TASKBAR      |
                     wx.CLIP_CHILDREN)

        if fwidgets.inSSHSession():
            style &= ~wx.FRAME_TOOL_WINDOW

        kwargs['style'] = style

        super().__init__(*args, **kwargs)


    def SetPaneWindow(self, pane):
        """Make sure that floated toolbars are sized correctly.
        """
        super().SetPaneWindow(pane)
        if isinstance(pane.window, ctrlpanel.ControlToolBar):
            size = self.GetBestSize()
            self.SetMaxSize(size)


def _AuiDockingGuide_init(self, *args, **kwargs):
    """I am also monkey-patching the
    ``wx.lib.agw.aui.AuiDockingGuide.__init__`` method, because in this
    instance, when running over SSH/X11, the ``wx.FRAME_TOOL_WINDOW`` style
    seems to result in the docking guide frames being given title bars, which
    is quite undesirable.

    I cannot patch the entire class in the aui package, because it is used
    as part of a class hierarchy. So I am just patching the method.
    """

    if 'style' in kwargs:
        style = kwargs['style']

    # This is the default style, as defined
    # in the AuiDockingGuide constructor
    else:
        style = (wx.FRAME_TOOL_WINDOW |
                 wx.FRAME_STAY_ON_TOP |
                 wx.FRAME_NO_TASKBAR  |
                 wx.NO_BORDER)

    if fwidgets.inSSHSession():
        style &= ~wx.FRAME_TOOL_WINDOW

    kwargs['style'] = style

    _AuiDockingGuide_real_init(self, *args, **kwargs)


if fwidgets.inSSHSession():
    aui  .AuiFloatingFrame       = MyAuiFloatingFrame
    auifm.AuiFloatingFrame       = MyAuiFloatingFrame
    _AuiDockingGuide_real_init   = aui.AuiDockingGuide.__init__
    aui.AuiDockingGuide.__init__ = _AuiDockingGuide_init
