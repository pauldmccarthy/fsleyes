#!/usr/bin/env python
#
# saveperspective.py - The SavePerspectiveAction
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SavePerspectiveAction` class, an action
which allows the user to save the current perspective.
"""

import wx

import fsl.data.strings         as strings
import                             action
import fsl.fsleyes.perspectives as perspectives


class SavePerspectiveAction(action.Action):
    """The ``SavePerspectiveAction`` allows the user to save the current
    :class:`.FSLEyesFrame` layout as a perspective, so it can be restored
    at a later time. See the :mod:`.perspectives` module.
    """

    def __init__(self, frame):
        """Create a ``SavePerspectiveAction``.

        :arg frame: The :class:`.FSLEyesFrame`.
        """

        self.__frame = frame
         
        action.Action.__init__(self, self.__savePerspective)

        
    def __savePerspective(self):
        """Save the current :class:`.FSLEyesFrame` layout as a perspective.
        The user is prompted to enter a name, and the current frame layout
        is saved via the :func:`.perspectives.savePerspective` function.
        """

        dlg = wx.TextEntryDialog(
            self.__frame,
            message=strings.messages['perspectives.savePerspective'])

        if dlg.ShowModal() != wx.ID_OK:
            return

        name = dlg.GetValue()

        if name.strip() == '':
            return

        # TODO Prevent using built-in perspective names

        # TODO Name collision - confirm overwrite

        perspectives.savePerspective(self.__frame, name)

        self.__frame.refreshPerspectiveMenu()
