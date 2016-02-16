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
        splashPanel     = imagepanel.ImagePanel(self, splashimg)
        authorLabel     = wx.StaticText(self)
        emailLabel      = wx.StaticText(self)
        companyLabel    = wx.StaticText(self)
        versionLabel    = wx.StaticText(self)
        glVersionLabel  = wx.StaticText(self)
        glRendererLabel = wx.StaticText(self)
        softwareField   = wx.TextCtrl(  self,
                                        size=(-1, 200),
                                        style=(wx.TE_LEFT      |
                                               wx.TE_RICH      | 
                                               wx.TE_MULTILINE |
                                               wx.TE_READONLY  |
                                               wx.TE_AUTO_URL))
        closeButton     = wx.Button(    self, id=wx.ID_CANCEL)

        # Set foreground/background colours
        objs = [self,
                authorLabel,
                emailLabel,
                companyLabel,
                versionLabel,
                glVersionLabel,
                glRendererLabel,
                softwareField]

        for obj in objs:
            obj.SetBackgroundColour('#000000')
            obj.SetForegroundColour('#ffffff')

        softwareField.SetDefaultStyle(wx.TextAttr('#ffffff', wx.NullColour))

        # Create / retrieve all the content
        verStr   = version.__version__
        glVerStr = gl.glGetString(gl.GL_VERSION)
        glRenStr = gl.glGetString(gl.GL_RENDERER)
        swlibs   = strings.about['libs']

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

        verStr   = strings.about['version']   .format(verStr)
        glVerStr = strings.about['glVersion'] .format(glVerStr)
        glRenStr = strings.about['glRenderer'].format(glRenStr)
        swStr    = strings.about['software']  .format(*swVersions)

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
        authorLabel    .SetLabel(strings.about['author'])
        emailLabel     .SetLabel(strings.about['email'])
        companyLabel   .SetLabel(strings.about['company'])
        versionLabel   .SetLabel(verStr)
        glVersionLabel .SetLabel(glVerStr)
        glRendererLabel.SetLabel(glRenStr)
        softwareField  .SetValue(swStr)
        closeButton    .SetLabel('Close')

        # Arrange the widgets
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        row1Sizer = wx.BoxSizer(wx.HORIZONTAL)
        row2Sizer = wx.BoxSizer(wx.HORIZONTAL)
        row3Sizer = wx.BoxSizer(wx.HORIZONTAL)
        row4Sizer = wx.BoxSizer(wx.HORIZONTAL)

        row1Sizer.Add(versionLabel,    flag=wx.EXPAND)
        row1Sizer.Add((1, 1),          flag=wx.EXPAND, proportion=1)
        row1Sizer.Add(authorLabel,     flag=wx.EXPAND)
 
        row2Sizer.Add(companyLabel,    flag=wx.EXPAND)
        row2Sizer.Add((1, 1),          flag=wx.EXPAND, proportion=1)
        row2Sizer.Add(emailLabel,      flag=wx.EXPAND)

        row3Sizer.Add(glVersionLabel,  flag=wx.EXPAND)
        row3Sizer.Add((1, 1),          flag=wx.EXPAND, proportion=1)
        
        row4Sizer.Add(glRendererLabel, flag=wx.EXPAND)
        row4Sizer.Add((1, 1),          flag=wx.EXPAND, proportion=1)

        rowargs = {'border' : 3,
                   'flag'   : wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM}

        mainSizer.Add(splashPanel)
        mainSizer.Add(row1Sizer,     **rowargs)
        mainSizer.Add(row2Sizer,     **rowargs)
        mainSizer.Add(row3Sizer,     **rowargs)
        mainSizer.Add(row4Sizer,     **rowargs)
        mainSizer.Add(softwareField, flag=wx.EXPAND, proportion=1)
        mainSizer.Add(closeButton,   flag=wx.EXPAND)

        self.SetSizer(mainSizer)
        self.Layout()
        self.Fit()
