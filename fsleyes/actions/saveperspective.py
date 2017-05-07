#!/usr/bin/env python
#
# saveperspective.py - The SavePerspectiveAction
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SavePerspectiveAction` class, an action
which allows the user to save the current perspective.
"""


import fsleyes.strings      as strings
import fsleyes.perspectives as perspectives
from . import                  base


class SavePerspectiveAction(base.Action):
    """The ``SavePerspectiveAction`` allows the user to save the current
    :class:`.FSLeyesFrame` layout as a perspective, so it can be restored
    at a later time. See the :mod:`.perspectives` module.
    """

    def __init__(self, frame):
        """Create a ``SavePerspectiveAction``.

        :arg frame: The :class:`.FSLeyesFrame`.
        """

        self.__frame = frame

        base.Action.__init__(self, self.__savePerspective)


    def __savePerspective(self):
        """Save the current :class:`.FSLeyesFrame` layout as a perspective.
        The user is prompted to enter a name, and the current frame layout
        is saved via the :func:`.perspectives.savePerspective` function.
        """

        import wx

        builtIns = list(perspectives.BUILT_IN_PERSPECTIVES.keys())
        saved    = perspectives.getAllPerspectives()

        while True:
            dlg = wx.TextEntryDialog(
                self.__frame,
                message=strings.messages[self, 'enterName'])

            if dlg.ShowModal() != wx.ID_OK:
                return

            name = dlg.GetValue()

            if name.strip() == '':
                return

            # Not allowed to use built-in perspective names
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

        perspectives.savePerspective(self.__frame, name)

        self.__frame.refreshPerspectiveMenu()
