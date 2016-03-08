#!/usr/bin/env python
#
# about.py - The AboutDialog class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.AboutDialog` class, a dialog which 
displays information about *FSLeyes*.
"""


import os.path   as op

import              wx
import OpenGL.GL as gl

import fsl.fsleyes.widgets.imagepanel as imagepanel
import fsl.data.strings               as strings
import fsl.version                    as version


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
        splashfile      = op.join(op.dirname(__file__),
                                  'icons', 'splash', 'splash.png')
        splashbmp       = wx.Bitmap(splashfile, wx.BITMAP_TYPE_PNG)
        splashimg       = splashbmp.ConvertToImage()

        # Create all the widgets
        splashPanel = imagepanel.ImagePanel(self, splashimg)
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
        textPanel.SetDefaultStyle(wx.TextAttr('#ffffff', wx.NullColour))

        # Create / retrieve all the content
        verStr    = version.__version__
        vcsVerStr = version.__vcs_version__
        glVerStr  = gl.glGetString(gl.GL_VERSION)
        glRenStr  = gl.glGetString(gl.GL_RENDERER)
        swlibs    = strings.about['libs']

        swVersions = []
        for lib in swlibs:

            try:
                mod = __import__(lib)
                if lib == 'PIL':
                    swVer = str(mod.PILLOW_VERSION)
                else:
                    swVer = str(mod.__version__)
            except:
                swVer = ''
            
            swVersions.append(swVer)

        verStr    = strings.about['version']   .format(verStr)
        vcsVerStr = strings.about['vcsVersion'].format(vcsVerStr)
        glVerStr  = strings.about['glVersion'] .format(glVerStr)
        glRenStr  = strings.about['glRenderer'].format(glRenStr)
        swStr     = strings.about['software']  .format(*swVersions)

        # Tack the license file contents onto
        # the end of the software description.
        licenseFile = op.join(op.dirname(__file__),
                              '..', '..', 'LICENSE')
        try:
            with open(licenseFile, 'rt') as f:
                licenseStr = f.read()
        except:
            licenseStr = ''

        swStr = swStr + '\n\n' + licenseStr
        swStr = swStr.strip()

        # Set the widget content
        infoStr = '\n'.join((verStr,
                             strings.about['company'],
                             strings.about['author'],
                             strings.about['email'],
                             vcsVerStr,
                             glVerStr,
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
