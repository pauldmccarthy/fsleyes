#!/usr/bin/env python
#
# loadannotations.py - Load annotations from file onto an OrthoPanel
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveAnnotationsActions` class, a FSLeyes
action which can be used to load :mod:`.annotations` from a file, for display
on an :class:`.OrthoPanel`.

Comprehensive documentation can be found in the :mod:`.saveannotations` module.
"""


import os
import sys
import shlex

import wx

import fsl.utils.settings       as fslsettings
import fsleyes.views.orthopanel as orthopanel
import fsleyes.actions          as actions
import fsleyes.strings          as strings


class LoadAnnotationsAction(actions.Action):
    """The ``LoadAnnotationsAction`` allos the user to load annotations
    from a file into an :class:`.OrthoPanel`.
    """


    @staticmethod
    def supportedViews():
        """This action is only intended to work with :class:`.OrthoPanel`
        views.
        """
        return [orthopanel.OrthoPanel]


    def __init__(self, overlayList, displayCtx, ortho):
        """Create a ``SaveAnnotationsAction``.

        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext`
        :arg ortho:       The :class:`.OrthoPanel`.
        """
        actions.Action.__init__(self, overlayList, displayCtx,
                                self.__loadAnnotations)
        self.__ortho = ortho


    def __loadAnnotations(self):
        """Show a dialog prompting the user for a file to load, then loads the
        annotations contained in the file and adds them to the
        :class:`OrthoPanel`.
        """

        ortho   = self.__ortho
        msg     = strings.messages[self, 'loadFile']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(wx.GetApp().GetTopWindow(),
                                message=msg,
                                defaultDir=fromDir,
                                style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()
