#!/usr/bin/env python
#
# savelayout.py - The SaveLayoutAction
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveLayoutAction` class, an action
which allows the user to save the current layout.
"""


import fsleyes.strings as strings
import fsleyes.layouts as layouts
from . import             base


class SaveLayoutAction(base.Action):
    """The ``SaveLayoutAction`` allows the user to save the current
    :class:`.FSLeyesFrame` layout, so it can be restored
    at a later time. See the :mod:`.layouts` module.
    """

    def __init__(self, frame):
        """Create a ``SaveLayoutAction``.

        :arg frame: The :class:`.FSLeyesFrame`.
        """

        self.__frame = frame

        base.Action.__init__(self, self.__saveLayout)


    def __saveLayout(self):
        """Save the current :class:`.FSLeyesFrame` layout.  The user is
        prompted to enter a name, and the current frame layout is saved
        via the :func:`.layouts.saveLayout` function.
        """

        import wx

        builtIns = list(layouts.BUILT_IN_LAYOUTS.keys())
        saved    = layouts.getAllLayouts()

        while True:
            dlg = wx.TextEntryDialog(
                self.__frame,
                message=strings.messages[self, 'enterName'])

            if dlg.ShowModal() != wx.ID_OK:
                return

            name = dlg.GetValue()

            if name.strip() == '':
                return

            # Not allowed to use built-in layout names
            if name in builtIns:
                dlg = wx.MessageDialog(
                    self.__frame,
                    message=strings.messages[
                        self, 'nameIsBuiltIn'].format(name),
                    style=(wx.ICON_EXCLAMATION | wx.OK))
                dlg.ShowModal()
                continue

            # Name collision - confirm overwrite
            if name in saved:
                dlg = wx.MessageDialog(
                    self.__frame,
                    message=strings.messages[
                        self, 'confirmOverwrite'].format(name),
                    style=(wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT))

                if dlg.ShowModal() == wx.ID_NO:
                    continue

            break

        layouts.saveLayout(self.__frame, name)

        self.__frame.refreshLayoutMenu()
