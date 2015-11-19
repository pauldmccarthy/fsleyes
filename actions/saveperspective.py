#!/usr/bin/env python
#
# saveperspective.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import wx

import fsl.data.strings         as strings
import fsl.fsleyes.actions      as actions
import fsl.fsleyes.perspectives as perspectives


class SavePerspectiveAction(actions.Action):
    """
    """

    def __init__(self, frame):
        """
        """

        self.__frame = frame
         
        actions.Action.__init__(self, self.__savePerspective)

        
    def __savePerspective(self):
        """
        """

        dlg = wx.TextEntryDialog(
            self.__frame,
            message=strings.messages['perspectives.savePerspective'])

        if dlg.ShowModal() != wx.ID_OK:
            return

        name = dlg.GetValue()

        if name.strip() == '':
            return

        perspectives.savePerspective(self.__frame, name)
