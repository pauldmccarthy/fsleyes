#!/usr/bin/env python


import wx

import fsleyes.views.viewpanel       as viewpanel
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.actions               as actions

PluginLayout = 'For a real plugin, this must be a valid FSLeyes layout string'


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

    # If you intend your tool to work with a specific view (e.g. an
    # OrthoPanel), override this method to return the supported view
    # types as a list, e.g.
    #
    # @staticmethod
    # def supportedViews():
    #     from fsleyes.views.orthopanel import OrthoPanel
    #     return [OrthoPanel]
    #
    # In this case, when your Tool is created, it will be passed a
    # reference to the view instance that your tool is associated with,
    # i.e. you should define __init__ as follows:
    #
    # def __init__(self, overlayList, displayCtx, view):
    #     ...
    #
    # If your tool is not associated with a view, you do not need
    # to implement the supportedViews method, and your __init__ method
    # will instead be passed a reference to the FSLeyesFrame, i.e.
    # you should define __init__ like so:
    #
    # def __init__(self, overlayList, displayCtx, frame):
    #     ...
    @staticmethod
    def supportedViews():
        return None

    def __init__(self, overlayList, displayCtx, frame):
        actions.Action.__init__(self, overlayList, displayCtx, self.run)

    def run(self):
        print('Running plugin tool')
