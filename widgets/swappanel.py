#!/usr/bin/env python
#
# swappanel.py - A wx.Panel which can contain many panels, but only displays
# one at a time. Pushing a button toggles the panel that is displayed.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx
import wx.lib.newevent as wxevent

_SwapPanelEvent, _EVT_SWAPPANEL_EVENT = wxevent.NewEvent()

EVT_SWAPPANEL_EVENT = _EVT_SWAPPANEL_EVENT

SwapPanelEvent = _SwapPanelEvent


class SwapPanel(wx.Panel):

    def __init__(self, parent, buttonSide=wx.TOP):

        wx.Panel.__init__(self, parent)
        
        self.__panels     = []
        self.__labels     = []
        self.__buttonSide = buttonSide
        self.__showing    = -1

        if buttonSide in (wx.TOP, wx.BOTTOM):
            self.__sizer = wx.BoxSizer(wx.VERTICAL)
        elif buttonSide in (wx.LEFT, wx.RIGHT):
            self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        else:
            raise ValueError('buttonSide must be one of wx.TOP, '
                             'wx.BOTTOM, wx.LEFT or wx.RIGHT') 

        self.__swapButton = wx.Button(self,
                                      label=u'\21BB',
                                      style=wx.BU_EXACTFIT)

        self.__swapButton.Bind(wx.EVT_BUTTON, self.__onSwap)

        self.SetSizer(self.__sizer)


    def Add(self, panel, label):
        self.__panels.append(panel)
        self.__labels.append(label)

        if len(self.__panels) == 1:
            self.__Show(0)

        
    def Remove(self, label):
        idx = self.__labels.index(label)

        self.__panels.pop(idx)
        self.__labels.pop(idx)


    def Show(self, label):
        idx = self.__labels.index(label)
        self.__Show(idx)


    def __Show(self, index):

        panel = self.__panels[index]

        self.__sizer.Clear()

        if self.__buttonSide in (wx.TOP, wx.LEFT):
            self.__sizer.Add(self.__swapButton, flag=wx.EXPAND)
            self.__sizer.Add(panel,             flag=wx.EXPAND, proportion=1)
            
        elif self.__buttonSide in (wx.BOTTOM, wx.RIGHT):
            self.__sizer.Add(self.__swapButton, flag=wx.EXPAND)
            self.__sizer.Add(panel,             flag=wx.EXPAND, proportion=1)

        self.Layout()


    def __onSwap(self, ev):
        self.__Show((self.__showing + 1) % len(self.__labels))
