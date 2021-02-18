#!/usr/bin/env python
#
# about.py - The AboutAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.AboutAction` class, an action which
displays an about dialog for *FSLeyes*.
"""


from . import base

import fsleyes_widgets as fwidgets


class AboutAction(base.Action):
    """The ``AboutAction`` class is an action which displays an
    :class:`.AboutDialog`, containing information about *FSLeyes*.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create an ``AboutAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The master :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        base.Action.__init__(self, overlayList, displayCtx, self.__showDialog)
        self.__frame = frame


    def __showDialog(self):
        """Creates and shows an :class:`.AboutDialog`. """

        import fsleyes.about as aboutdlg

        dlg = aboutdlg.AboutDialog(self.__frame)
        dlg.Show()

        # When running over X11/SSH, CentreOnParent
        # causes the dialog to be moved way off.
        if not fwidgets.inSSHSession():
            dlg.CentreOnParent()
