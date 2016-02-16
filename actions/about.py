#!/usr/bin/env python
#
# about.py - The AboutAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.AboutAction` class, an action which
displays an about dialog for *FSLeyes*.
"""


import                      action
import fsl.fsleyes.about as aboutdlg


class AboutAction(action.Action):
    """The ``AboutAction`` class is an action which displays an
    :class:`.AboutDialog`, containing information about *FSLeyes*.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create an ``AboutAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The master :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """

        action.Action.__init__(self, self.__showDialog)

        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx 


    def __showDialog(self):
        """Creates and shows an :class:`.AboutDialog`. """

        dlg = aboutdlg.AboutDialog(self.__frame)
        dlg.Show()
        dlg.CentreOnParent()
