#!/usr/bin/env python
#
# clearsettings.py - The ClearSettingsAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ClearSettingsAction` class, an action
which clears all settings from the :mod:`fsl.utils.settings` module.
"""


import fsl.utils.settings as fslsettings
import fsleyes.strings    as strings
from . import                base


class ClearSettingsAction(base.Action):
    """The ``ClearSettingsAction`` class is an action which clears all
    settings from the :mod:`fsl.utils.settings` module.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``ClearSettingsAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(
            self, overlayList, displayCtx, self.__clearSettings)
        self.__frame = frame


    def __clearSettings(self):
        """Ask the user to confirm, then clear  all settings stored by the
        :mod:`fsl.utils.settings` module.
        """

        import wx

        msg    = strings.messages[self, 'confirm']
        title  = strings.titles[  self, 'confirm']

        dlg = wx.MessageDialog(self.__frame,
                               message=msg,
                               caption=title,
                               style=(wx.YES_NO        |
                                      wx.NO_DEFAULT    |
                                      wx.CENTRE        |
                                      wx.ICON_WARNING))

        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_NO:
            return

        fslsettings.clear()
