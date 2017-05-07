#!/usr/bin/env python
#
# clearperspectives.py - The ClearPerspectiveAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ClearPerspectiveAction`, which allows
the user to clear/delete all saved perspectives.
"""


import fsleyes.strings      as strings
import fsleyes.perspectives as perspectives
from . import                  base


class ClearPerspectiveAction(base.Action):
    """The ``ClearPerspectiveAction`` allows the user to delete all saved
    perspectives.
    """

    def __init__(self, frame):
        """Create a ``ClearPerspectiveAction``. """
        base.Action.__init__(self, func=self.__clearPerspectives)

        self.__frame = frame


    def __clearPerspectives(self):
        """Deletes all saved perspectives. Gets the user to confirm that
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

        for p in perspectives.getAllPerspectives():
            perspectives.removePerspective(p)

        self.__frame.refreshPerspectiveMenu()
