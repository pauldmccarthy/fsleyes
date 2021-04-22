#!/usr/bin/env python
#
# splash.py - FSLeyes splash screen.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLeyesSplash` class, a splash screen for
*FSLeyes*.
"""


import            time
import os.path as op

import wx

import                               fsleyes
import fsleyes_widgets.imagepanel as imagepanel
import fsleyes.strings            as strings


def getSplashFile():
    """Returns the path to the splash screen image file. """
    return op.join(fsleyes.assetDir, 'icons', 'splash', 'splash.png')


class FSLeyesSplash(wx.Frame):
    """A simple splash screen for *FSLeyes*. An image and a status bar are
    displayed; the status bar can be updated via the :meth:`SetStatus` method.


    The :class:`.ImagePanel` class is used to display the image.


    Typical usage would be something like the following::

        splash = FSLeyesSplash(None)
        splash.Show()

        # Do something, e.g. loading overlays
        splash.SetStatus('Loading blah.nii.gz ...')

        # Finished initialising, the application is ready
        splash.Close()
    """

    def __init__(self, parent):
        """Create a ``FSLeyesSplash`` frame.

        :arg parent: The :mod:`wx` parent object.
        """

        wx.Frame.__init__(self, parent, style=wx.FULL_REPAINT_ON_RESIZE)

        splashbmp  = wx.Bitmap(getSplashFile(), wx.BITMAP_TYPE_PNG)
        splashimg  = splashbmp.ConvertToImage()

        self.__splashPanel = imagepanel.ImagePanel(self, splashimg)
        self.__splashPanel.SetMinSize(splashimg.GetSize())
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


    def Show(self):
        """Show this ``FSLeyesSplash`` frame, and centre it on the screen. """

        wx.Frame.Show(self)
        self.CentreOnScreen()
        self.Refresh()
        self.Update()

        # GTK is a piece of shit. Refresh/Update, combined
        # with a straight call to Yield does not guarantee
        # that the splash screen will be displayed. It
        # seems that a short delay is necessary before it
        # will be drawn, during which time we can't do
        # anything which would block the application loop.
        for i in range(10):
            wx.GetApp().Yield()
            time.sleep(0.025)


    def SetStatus(self, text):
        """Sets the text shown on the status bar to the specified ``text``. """
        self.__statusBar.SetLabel(text)
        self.__statusBar.Refresh()
        self.__statusBar.Update()
