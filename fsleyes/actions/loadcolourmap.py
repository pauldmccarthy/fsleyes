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

import fsl.utils.settings as fslsettings

import fsleyes            as fsleyes
import fsleyes.strings    as strings
import fsleyes.colourmaps as fslcmap
from . import                base


log = logging.getLogger(__name__)


_stringID = 'actions.loadcolourmap.'


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
        base.Action.__init__(self, self.__loadColourMap)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx 

        
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
        loadDir = fslsettings.read('fsleyes.loadcolourmap', os.getcwd())

        # prompt the user to choose a colour map file
        dlg = wx.FileDialog(
            app.GetTopWindow(),
            defaultDir=loadDir,
            message=strings.messages[_stringID + 'loadcmap'],
            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        # prompt the user to choose  a name for the colour
        # map (using the filename prefix as the default)
        cmapFile = dlg.GetPath()
        cmapDir  = op.dirname(cmapFile)
        cmapName = op.splitext(op.basename(cmapFile))[0]

        cmapNameMsg = strings.messages[_stringID + 'namecmap']

        while True:

            dlg = wx.TextEntryDialog(
                app.GetTopWindow(),
                message=cmapNameMsg,
                defaultValue=cmapName)

            if dlg.ShowModal() != wx.ID_OK:
                return

            cmapName = dlg.GetValue()

            # a colour map with the specified name already exists
            if fslcmap.isColourMapRegistered(cmapName):
                cmapNameMsg = strings.messages[_stringID + 'alreadyinstalled']
                continue

            # colour map names must only contain 
            # letters, numbers, and underscores
            if not cmapName.replace('_', '').isalnum():
                cmapNameMsg = strings.messages[_stringID + 'invalidname']
                continue

            break

        # register the selected colour map file
        fslcmap.registerColourMap(cmapFile,
                                  self.__overlayList,
                                  self.__displayCtx,
                                  cmapName)

        # Save the directory for next time
        fslsettings.write('fsleyes.loadcolourmap', cmapDir)

        # Does this user have permission to write 
        # to FSLeyes assets? If not, don't bother 
        # asking them whether they want to install 
        # the colour map, because (at this point 
        # in time) they can't.
        if not fsleyes.canWriteToAssetDir():
            return

        # ask the user if they want to install
        # the colour map for future use
        dlg = wx.MessageDialog(
            app.GetTopWindow(),
            caption=strings.titles[  self,       'installcmap'],
            message=strings.messages[_stringID + 'installcmap'],
            style=wx.YES_NO)

        if dlg.ShowModal() != wx.ID_YES:
            return

        # install the colour map
        try:
            fslcmap.installColourMap(cmapName)
            
        except Exception as e:
            log.warn('Error installing colour map: {}'.format(e))
            wx.MessageDialog(
                app.GetTopWindow(),
                message='{}: {}'.format(
                    strings.messages[_stringID + 'installerror'], str(e)),
                style=wx.ICON_ERROR).ShowModal()
