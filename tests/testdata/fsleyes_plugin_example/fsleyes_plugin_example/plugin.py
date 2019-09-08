#!/usr/bin/env python


import wx

import fsleyes.views.viewpanel       as viewpanel
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.actions               as actions


class PluginView(viewpanel.ViewPanel):

    def __init__(self, *args, **kwargs):
        viewpanel.ViewPanel.__init__(self, *args, **kwargs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(wx.StaticText(self, label='Plugin View'),
                  flag=wx.EXPAND, proportion=1)


class PluginControl(ctrlpanel.ControlPanel):

    def __init__(self, *args, **kwargs):
        ctrlpanel.ControlPanel.__init__(self, *args, **kwargs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(wx.StaticText(self, label='Plugin Control'),
                  flag=wx.EXPAND, proportion=1)


    @staticmethod
    def defaultLayout():
        return {
            'location' : wx.LEFT,
        }


    @staticmethod
    def supportedViews():
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


class PluginTool(actions.Action):

    def __init__(self, overlayList, displayCtx, frame):
        actions.Action.__init__(self, overlayList, displayCtx, self.run)

    def run(self):
        print('Running plugin tool')
