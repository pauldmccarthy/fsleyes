#!/usr/bin/env python
#
# about.py - The AboutDialog class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.AboutDialog` class, a dialog which
displays information about *FSLeyes*.
"""


import os.path as op

import wx

import fsleyes_widgets.imagepanel         as imagepanel
from   fsl.utils.platform import platform as fslplatform
import fsleyes.strings                    as strings
import fsleyes.splash                     as splash
import fsleyes.version                    as version


class AboutDialog(wx.Dialog):
    """The ``AboutDialog`` is a dialog which displays information about
    *FSLeyes*.
    """

    def __init__(self, parent):
        """Create an ``AboutDialog``.

        :arg parent: ``wx`` parent object.
        """
        wx.Dialog.__init__(self, parent, title=strings.about['title'])

        # Load the splash screen
        splashbmp = wx.Bitmap(splash.getSplashFile(), wx.BITMAP_TYPE_PNG)
        splashimg = splashbmp.ConvertToImage()

        # Create all the widgets
        splashPanel = imagepanel.ImagePanel(self, splashimg)
        splashPanel.SetMinSize(splashimg.GetSize())

        textPanel   = wx.TextCtrl(self,
                                  size=(-1, 200),
                                  style=(wx.TE_LEFT      |
                                         wx.TE_RICH      |
                                         wx.TE_MULTILINE |
                                         wx.TE_READONLY  |
                                         wx.TE_AUTO_URL))
        closeButton = wx.Button(self, id=wx.ID_CANCEL)

        # Set foreground/background colours
        textPanel.SetBackgroundColour('#000000')
        textPanel.SetForegroundColour('#ffffff')
        textPanel.SetDefaultStyle(wx.TextAttr('#ffffff', '#000000'))

        # Create / retrieve all the content
        verStr    = version.__version__
        glVerStr  = fslplatform.glVersion
        glRenStr  = fslplatform.glRenderer
        swlibs    = strings.about['libs']

        swVersions = []
        for lib in swlibs:

            try:
                mod = __import__(lib)

                # Retrieve the sub-module if necessary
                for n in lib.split(".")[1:]:
                    mod = getattr(mod, n)

                if lib == 'PIL':
                    swVer = str(mod.PILLOW_VERSION)
                else:
                    swVer = str(mod.__version__)
            except Exception:
                swVer = ''

            swVersions.append(swVer)

        verStr    = strings.about['version']   .format(verStr)
        fslVer    = strings.about['fslVersion'].format(fslplatform.fslVersion)
        fslDir    = strings.about['fslPath']   .format(fslplatform.fsldir)
        glVerStr  = strings.about['glVersion'] .format(glVerStr)
        glCompat  = strings.about['glCompat']  .format(fslplatform.glVersion)
        glRenStr  = strings.about['glRenderer'].format(glRenStr)
        swStr     = strings.about['software']  .format(*swVersions)

        # Tack the license file contents onto
        # the end of the software description.
        licenseFile = op.join(op.dirname(__file__),
                              '..', '..', 'LICENSE')
        try:
            with open(licenseFile, 'rt') as f:
                licenseStr = f.read()
        except Exception:
            licenseStr = ''

        swStr = swStr + '\n\n' + licenseStr
        swStr = swStr.strip()

        # Set the widget content
        infoStr = '\n'.join((verStr,
                             strings.about['company'],
                             strings.about['author'],
                             strings.about['email'],
                             fslVer,
                             fslDir,
                             glVerStr,
                             glCompat,
                             glRenStr))

        textPanel  .SetValue(infoStr + '\n\n' + swStr)
        closeButton.SetLabel('Close')

        # Arrange the widgets
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(splashPanel)
        sizer.Add(textPanel, flag=wx.EXPAND, proportion=1)
        sizer.Add(closeButton, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
