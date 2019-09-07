#!/usr/bin/env python
#
# loadcolourmap.py - Load a colour map file.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadColourMapAction`, which allows the
user to load a new colour map.
"""

import            logging
import            os
import os.path as op

import fsl.utils.settings           as fslsettings
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
import fsleyes.colourmaps           as fslcmap
from . import                          base


log = logging.getLogger(__name__)


class LoadColourMapAction(base.Action):
    """The ``LoadColourMapAction`` allows the user to select a colour
    map file and give it a name.

    The loaded colour map is then registered with the :mod:`.colourmaps`
    module. The user is also given the option to permanently save the
    loaded colour map in *FSLeyes*.
    """


    def __init__(self, overlayList, displayCtx):
        """Create a ``LoadColourMapAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        base.Action.__init__(
            self, overlayList, displayCtx, self.__loadColourMap)


    def __loadColourMap(self):
        """This method does the following:

        1. Prompts the user to select a colour map file

        2. Prompts the user to name the new colour map.

        3. Registers the colour map with the :mod:`.colourmaps` module.

        4. Asks the user if they want the colour map installed, and installs
           it if they do.
        """

        import wx

        app = wx.GetApp()

        # Get the most recent colour map
        # directory if there is one
        loadDir = fslsettings.read('fsleyes.loadcolourmapdir', os.getcwd())

        # prompt the user to choose a colour map file
        dlg = wx.FileDialog(
            app.GetTopWindow(),
            defaultDir=loadDir,
            message=strings.messages[self, 'loadcmap'],
            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        # prompt the user to choose  a name for the colour
        # map (using the filename prefix as the default)
        cmapFile = dlg.GetPath()
        cmapDir  = op.dirname(cmapFile)
        cmapName = op.splitext(op.basename(cmapFile))[0]

        cmapNameMsg   = strings.messages[self, 'namecmap']
        cmapNameTitle = strings.titles[  self, 'namecmap']

        while True:

            dlg = wx.TextEntryDialog(
                app.GetTopWindow(),
                cmapNameMsg,
                cmapNameTitle,
                cmapName)

            if dlg.ShowModal() != wx.ID_OK:
                return

            cmapName = dlg.GetValue()
            cmapKey  = fslcmap.makeValidMapKey(cmapName)

            # a colour map with the specified name already exists
            if fslcmap.isColourMapRegistered(cmapKey):
                cmapNameMsg = strings.messages[self, 'alreadyinstalled']
                continue

            break

        # register the selected colour map file
        fslcmap.registerColourMap(cmapFile,
                                  self.overlayList,
                                  self.displayCtx,
                                  key=cmapKey,
                                  name=cmapName)

        # Save the directory for next time
        fslsettings.write('fsleyes.loadcolourmapdir', cmapDir)

        # ask the user if they want to install
        # the colour map for future use
        dlg = wx.MessageDialog(
            app.GetTopWindow(),
            caption=strings.titles[  self, 'installcmap'],
            message=strings.messages[self, 'installcmap'],
            style=wx.YES_NO)

        if dlg.ShowModal() != wx.ID_YES:
            return

        # install the colour map
        etitle = strings.titles[  self, 'installerror']
        emsg   = strings.messages[self, 'installerror']

        with status.reportIfError(title=etitle, msg=emsg, raiseError=False):
            fslcmap.installColourMap(cmapKey)
