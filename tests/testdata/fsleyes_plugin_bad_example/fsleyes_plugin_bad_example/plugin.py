#!/usr/bin/env python


import wx

import fsleyes.panel as fslpanel


class PluginView(fslpanel.FSLeyesPanel):

    def __init__(self, *args, **kwargs):
        fslpanel.FSLeyesPanel.__init__(self, *args, **kwargs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(wx.StaticText(self, label='Plugin View'),
                  flag=wx.EXPAND, proportion=1)


class PluginControl(wx.Panel):

    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(wx.StaticText(self, label='Plugin Control'),
                  flag=wx.EXPAND, proportion=1)


class PluginTool(object):
    def __call__(self, *args, **kwargs):
        print('Running plugin tool')
