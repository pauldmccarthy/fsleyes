#!/usr/bin/env python


import                                     wx
import wx.lib.agw.aui                     as aui
import wx.lib.agw.aui.framemanager        as auifm
from   fsl.utils.platform import platform as fslplatform
import fsleyes_widgets                    as fwidgets
import fsleyes.controls.controlpanel      as ctrlpanel


class MyAuiFloatingFrame(auifm.AuiFloatingFrame):
    """Here I am monkey patching the
    ``wx.agw.aui.framemanager.AuiFloatingFrame.__init__`` method.

    The ``wx.FRAME_TOOL_WINDOW`` style, as passed to the ``wx.MiniFrame``
    constructor (from which the ``AuiFloatingFrame`` class derives) seems to
    cause problems in various environments.

    When this style flag is active:

     - When running over an SSH/X11 session using XQuartz running on macOS,
       When a combobox is embedded in a floating frame (either a pane or a
       toolbar), its dropdown list appears underneath the frame, meaning that
       the user is unable to actually select any items from the list!

     - When running under the Windows wslg wayland servver (with
       GDK_BACKEND=x11, which is required for versions of wxPython/wxWidgets
       that have been compiled to use GLX for OpenGL), all ``wx.MiniFrame``
       instances seem to be completely unresponsive to user interaction.

    Removing this style flag seems to resolve both of the above problems, so
    this is exactly what I'm doing. I haven't looked any deeper into the
    situation.

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

        # disable FRAME_TOOL_WINDOW if
        # running over X11/SSH or in WSL
        style &= ~wx.FRAME_TOOL_WINDOW

        kwargs['style'] = style

        super().__init__(*args, **kwargs)


    def SetPaneWindow(self, pane):
        """Make sure that floated toolbars are sized correctly. """
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

    # Disable wx.FRAME_TOOL_WINDOW style
    style &= ~wx.FRAME_TOOL_WINDOW

    kwargs['style'] = style

    _AuiDockingGuide_real_init(self, *args, **kwargs)


if fwidgets.inSSHSession() or fslplatform.wsl:
    aui  .AuiFloatingFrame       = MyAuiFloatingFrame
    auifm.AuiFloatingFrame       = MyAuiFloatingFrame
    _AuiDockingGuide_real_init   = aui.AuiDockingGuide.__init__
    aui.AuiDockingGuide.__init__ = _AuiDockingGuide_init
