#!/usr/bin/env python
#
# splash.py - FSLeyes splash screen.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLEyesSplash` class, a splash screen for
*FSLeyes*.
"""


import os.path as op

import wx

import fsl.utils.imagepanel as imagepanel
import fsl.fsleyes.strings  as strings


class FSLEyesSplash(wx.Frame):
    """A simple splash screen for *FSLeyes*. An image and a status bar are
    displayed; the status bar can be updated via the :meth:`SetStatus` method.

    
    The :class:`.ImagePanel` class is used to display the image.

    
    Typical usage would be something like the following::

        splash = FSLEyesSplash(None)
        splash.Show()

        # Do something, e.g. loading overlays
        splash.SetStatus('Loading blah.nii.gz ...')

        # Finished initialising, the application is ready
        splash.Close()
    """
    
    def __init__(self, parent):
        """Create a ``FSLEyesSplash`` frame.

        :arg parent: The :mod:`wx` parent object.
        """
        
        wx.Frame.__init__(self, parent, style=0)

        splashfile = op.join(op.dirname(__file__),
                             'icons', 'splash', 'splash.png')
        splashbmp  = wx.Bitmap(splashfile, wx.BITMAP_TYPE_PNG)
        splashimg  = splashbmp.ConvertToImage()
    
        self.__splashPanel = imagepanel.ImagePanel(self, splashimg)
        self.__statusBar   = wx.StaticText(self, style=wx.ST_ELLIPSIZE_MIDDLE)
        
        self.__statusBar.SetLabel(strings.messages[self, 'default'])

        self.__statusBar.SetBackgroundColour('#000000')
        self.__statusBar.SetForegroundColour('#ffffff')
        self            .SetBackgroundColour('#000000')
        
        self.__sizer = wx.BoxSizer(wx.VERTICAL)

        self.__sizer.Add(self.__splashPanel, flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__statusBar,   flag=wx.EXPAND)

        self.SetSizer(self.__sizer)

        self.Layout()
        self.Fit()

        
    def SetStatus(self, text):
        """Sets the text shown on the status bar to the specified ``text``. """
        self.__statusBar.SetLabel(text)
        self.__statusBar.Refresh()
        self.__statusBar.Update()
