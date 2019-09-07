#!/usr/bin/env python
#
# clearlayouts.py - The ClearLayoutsAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ClearLayoutsAction`, which allows
the user to clear/delete all saved layouts.
"""


import fsleyes.strings as strings
import fsleyes.layouts as layouts
from . import             base


class ClearLayoutsAction(base.Action):
    """The ``ClearLayoutsAction`` allows the user to delete all saved
    layouts.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``ClearLayoutsAction``. """
        base.Action.__init__(
            self, overlayList, displayCtx, func=self.__clearLayouts)
        self.__frame = frame


    def __clearLayouts(self):
        """Deletes all saved layouts. Gets the user to confirm that
        they want to proceed before doing so.
        """

        import wx

        dlg = wx.MessageDialog(
            wx.GetTopLevelWindows()[0],
            message=strings.messages[self, 'confirmClear'],
            caption=strings.titles[  self, 'confirmClear'],
            style=(wx.ICON_WARNING |
                   wx.YES_NO       |
                   wx.NO_DEFAULT))

        if dlg.ShowModal() != wx.ID_YES:
            return

        for l in layouts.getAllLayouts():
            layouts.removeLayout(l)

        self.__frame.refreshLayoutMenu()
