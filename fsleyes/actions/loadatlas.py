#!/usr/bin/env python
#
# loadatlas.py - The LoadAtlas action.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadAtlasAction`, an action which
allows the user to load an atlas specification into FSLeyes. See the
:mod:`fsl.data.atlases` module.
"""


import fsl.data.atlases as atlases

import fsleyes.strings as  strings
from . import              action


class LoadAtlasAction(action.Action):
    """The ``LoadAtlasAction`` prompts the user to select a FSL atlas
    specification file. This file is then passed to the
    :func:`.fsl.data.atlases.addAtlas` function, to add the atlas
    to the :class:`.AtlasRegistry`.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``LoadAtlasAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        action.Action.__init__(self, self.__loadAtlas)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx 


    def __loadAtlas(self):
        """Prompts the user to select an atlas specification file, and then
        loads the atlas.
        """

        import wx
        app = wx.GetApp()

        msg = strings.titles[self, 'fileDialog']
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message=msg,
                            wildcard='XML atlas specification|*.xml',
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        path = dlg.GetPath()

        try:
            atlases.addAtlas(path)
            
        except Exception as e:

            title = strings.titles[  self, 'error']
            msg   = strings.messages[self, 'error'].format(path, str(e))

            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 
