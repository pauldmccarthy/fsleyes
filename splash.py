#!/usr/bin/env python
#
# splash.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op


import wx


import fsl.fsleyes.widgets.imagepanel as imagepanel
import fsl.data.strings               as strings


class FSLEyesSplash(wx.Frame):
    
    def __init__(self, parent):
        
        wx.Frame.__init__(self, parent, style=0)
        
        splashfile = op.join(op.dirname(__file__), 'splash.png')
        splashbmp  = wx.Bitmap(splashfile, wx.BITMAP_TYPE_PNG)
        splashimg  = splashbmp.ConvertToImage()
    
        splashPanel    = imagepanel.ImagePanel(self, splashimg)
        self.statusBar = wx.StaticText(self, style=wx.ELLIPSIZE_MIDDLE)
        self.statusBar.SetLabel(strings.messages[self, 'default'])

        self.statusBar.SetBackgroundColour('white')
        self          .SetBackgroundColour('white')
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(splashPanel,    flag=wx.EXPAND, proportion=1)
        sizer.Add(self.statusBar, flag=wx.EXPAND)

        self.SetSizer(sizer)

        self.Layout()
        self.Fit()

    def SetStatus(self, text):
        self.statusBar.SetLabel(text)
