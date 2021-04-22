#!/usr/bin/env python
#
# loadplugin.py - The LoadPluginAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadPluginAction` class, an action which
allows the user to load/install FSLeyes plugins.
"""


import os.path as op
import            os

import wx

import fsl.utils.settings           as fslsettings
import fsleyes_widgets.utils.status as status
import fsleyes.plugins              as plugins
import fsleyes.strings              as strings
from . import                          base


class LoadPluginAction(base.Action):
    """The :class:`LoadPluginAction` class is an :class:`.Action` which allows
    the user to load/install FSLeyes plugins - see the :mod:`.plugins` module.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``LoadPluginAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The top-level :class:`.DisplayContext`.
        :arg overlayList: The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, overlayList, displayCtx, self.__loadPlugin)
        self.__frame = frame


    def __loadPlugin(self, *args, **kwargs):
        """Prompts the user to select a plugin file, asks them whether they
        would like to install it permanently, and then passes it to either
        :func:`.loadPlugin` or :func:`.installPlugin`.
        """

        lastDir = fslsettings.read('loadPluginLastDir')

        if lastDir is None:
            lastDir = os.getcwd()

        msg = strings.messages[self, 'loadPlugin']
        dlg = wx.FileDialog(self.__frame,
                            message=msg,
                            defaultDir=lastDir,
                            wildcard='*.py',
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        fname = dlg.GetPath()

        fslsettings.write('loadPluginLastDir', op.dirname(fname))

        dlg = wx.MessageDialog(
            self.__frame,
            caption=strings.titles[  self, 'installPlugin'],
            message=strings.messages[self, 'installPlugin'],
            style=wx.YES_NO | wx.CANCEL)

        result = dlg.ShowModal()

        if result == wx.ID_YES:
            etitle = strings.titles[  self, 'installError']
            emsg   = strings.messages[self, 'installError']
            func   = plugins.installPlugin
        elif result == wx.ID_NO:
            etitle = strings.titles[  self, 'loadError']
            emsg   = strings.messages[self, 'loadError']
            func   = plugins.loadPlugin
        else:
            return

        with status.reportIfError(title=etitle, msg=emsg, raiseError=False):
            func(fname)

        for panel in self.__frame.viewPanels:
            panel.reloadPlugins()

        self.__frame.refreshViewMenu()
        self.__frame.refreshToolsMenu()
        self.__frame.refreshSettingsMenu()
