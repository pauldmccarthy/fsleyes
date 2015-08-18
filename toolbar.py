#!/usr/bin/env python
#
# toolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import wx.lib.newevent as wxevent

import numpy as np

import fsl.fsleyes.panel   as fslpanel
import fsl.fsleyes.icons   as icons


log = logging.getLogger(__name__)


_ToolBarEvent, _EVT_TOOLBAR_EVENT = wxevent.NewEvent()


EVT_TOOLBAR_EVENT = _EVT_TOOLBAR_EVENT
"""Identifier for the :data:`ToolBarEvent` event. """


ToolBarEvent = _ToolBarEvent
"""Event emitted when one or more tools is/are added/removed to/from the
toolbar.
"""


class FSLEyesToolBar(fslpanel._FSLEyesPanel, wx.PyPanel):
    """
    """


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 height=32,
                 actionz=None):
        wx.PyPanel.__init__(self, parent)
        fslpanel._FSLEyesPanel.__init__(self, overlayList, displayCtx, actionz)

        self.__tools      = []
        self.__index      = 0
        self.__numVisible = None

        font = self.GetFont()
        self.SetFont(font.Smaller())

        # BU_NOTEXT causes segfault under OSX
        if wx.Platform == '__WXMAC__': style = wx.BU_EXACTFIT 
        else:                          style = wx.BU_EXACTFIT | wx.BU_NOTEXT
            
        lBmp = icons.loadBitmap('thinLeftArrow{}' .format(height))
        rBmp = icons.loadBitmap('thinRightArrow{}'.format(height))
        self.__leftButton  = wx.Button(self, style=style)
        self.__rightButton = wx.Button(self, style=style)

        self.__leftButton.SetBitmap(lBmp)
        self.__rightButton.SetBitmap(rBmp)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer) 

        self.__leftButton .Bind(wx.EVT_BUTTON,     self.__onLeftButton)
        self.__rightButton.Bind(wx.EVT_BUTTON,     self.__onRightButton)
        self              .Bind(wx.EVT_MOUSEWHEEL, self.__onMouseWheel)
        self              .Bind(wx.EVT_SIZE,       self.__drawToolBar)
        

    def __onMouseWheel(self, ev):

        wheelDir = ev.GetWheelRotation()
        if   wheelDir < 0: self.__onRightButton()
        elif wheelDir > 0: self.__onLeftButton()


    def __onLeftButton(self, ev=None):

        self.__index -= 1

        if self.__index <= 0:
            self.__index = 0

        log.debug('Left button pushed - setting start '
                  'tool index to {}'.format(self.__index)) 

        self.__drawToolBar()

        
    def __onRightButton(self, ev=None):
        
        self.__index += 1

        if self.__index + self.__numVisible >= len(self.__tools):
            self.__index = len(self.__tools) - self.__numVisible

        log.debug('Right button pushed - setting start '
                  'tool index to {}'.format(self.__index))

        self.__drawToolBar()


    def __drawToolBar(self, *a):

        sizer = self.__sizer
        tools = self.__tools

        sizer.Clear()
        
        availWidth = self.GetSize().GetWidth()
        reqdWidths = [tool.GetBestSize().GetWidth() for tool in tools]
        leftWidth  = self.__leftButton .GetBestSize().GetWidth()
        rightWidth = self.__rightButton.GetBestSize().GetWidth()

        if availWidth >= sum(reqdWidths):

            log.debug('{}: All tools fit ({} >= {})'.format(
                type(self).__name__, availWidth, sum(reqdWidths)))
            
            self.__index      = 0
            self.__numVisible = len(tools)
            
            self.__leftButton .Enable(False)
            self.__rightButton.Enable(False)
            self.__leftButton .Show(  False)
            self.__rightButton.Show(  False) 

            for tool in tools:
                tool.Show(True)
                sizer.Add(tool, flag=wx.ALIGN_CENTRE)

        else:
            reqdWidths = reqdWidths[self.__index:]
            cumWidths  = np.cumsum(reqdWidths) + leftWidth + rightWidth
            biggerIdxs = np.where(cumWidths > availWidth)[0]

            if len(biggerIdxs) == 0:
                lastIdx = len(tools)
            else:
                lastIdx = biggerIdxs[0] + self.__index
            
            self.__numVisible = lastIdx - self.__index

            log.debug('{}: {} tools fit ({} - {})'.format(
                type(self).__name__, self.__numVisible, self.__index, lastIdx))

            self.__leftButton .Show(True)
            self.__rightButton.Show(True)
            self.__leftButton .Enable(self.__index > 0)
            self.__rightButton.Enable(lastIdx < len(tools))

            for i in range(len(tools)):
                if i >= self.__index and i < lastIdx:
                    tools[i].Show(True)
                    sizer.Add(tools[i], flag=wx.ALIGN_CENTRE)
                else:
                    tools[i].Show(False)

        sizer.Insert(self.__numVisible, (0, 0), flag=wx.EXPAND, proportion=1)
        sizer.Insert(self.__numVisible + 1, self.__rightButton, flag=wx.EXPAND)
        sizer.Insert(0,                     self.__leftButton,  flag=wx.EXPAND)

        self.Layout()



    def MakeLabelledTool(self, tool, labelText, labelSide=wx.TOP):

        if   labelSide in (wx.TOP,  wx.BOTTOM): orient = wx.VERTICAL
        elif labelSide in (wx.LEFT, wx.RIGHT):  orient = wx.HORIZONTAL
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(orient)

        panel.SetSizer(sizer)
        tool.Reparent(panel)

        label = wx.StaticText(panel)
        label.SetLabel(labelText)

        if labelSide in (wx.TOP, wx.LEFT):
            sizer.Add(label, flag=wx.ALIGN_CENTRE)
            sizer.Add(tool,  flag=wx.ALIGN_CENTRE)
        else:
            sizer.Add(tool,  flag=wx.ALIGN_CENTRE)
            sizer.Add(label, flag=wx.ALIGN_CENTRE) 

        return panel


    def Enable(self, *args, **kwargs):
        wx.PyPanel.Enable(self, *args, **kwargs)
        for t in self.__tools:
            t.Enable(*args, **kwargs)

            
    def GetTools(self):
        """
        """
        return self.__tools[:]


    def AddTool(self, tool):
        self.InsertTool(tool)

        
    def InsertTools(self, tools, index=None):

        for i, tool in enumerate(tools, index):
            self.InsertTool(tool, i, postevent=False)

        wx.PostEvent(self, ToolBarEvent())


    def SetTools(self, tools, destroy=False):

        self.ClearTools(destroy, postevent=False)

        for tool in tools:
            self.InsertTool(tool, postevent=False)

        wx.PostEvent(self, ToolBarEvent())
        

    def InsertTool(self, tool, index=None, postevent=True):

        if index is None:
            index = len(self.__tools)

        log.debug('{}: adding tool at index {}: {}'.format(
            type(self).__name__, index, type(tool).__name__))

        tool.Bind(wx.EVT_MOUSEWHEEL, self.__onMouseWheel)

        self.__tools.insert(index, tool)

        self.InvalidateBestSize()
        self.__drawToolBar()

        if postevent:
            wx.PostEvent(self, ToolBarEvent())
            

    def DoGetBestSize(self):
        # Calculate the minimum/maximum size
        # for this toolbar, given the addition
        # of the new tool
        ttlWidth  = 0
        minWidth  = 0
        minHeight = 0

        for tool in self.__tools:
            tw, th = tool.GetBestSize().Get()
            if tw > minWidth:  minWidth  = tw
            if th > minHeight: minHeight = th

            ttlWidth += tw

        leftWidth  = self.__leftButton .GetBestSize().GetWidth()
        rightWidth = self.__rightButton.GetBestSize().GetWidth()

        minWidth = minWidth + leftWidth + rightWidth

        # The agw.AuiManager does not honour the best size when
        # toolbars are floated, but it does honour the minimum
        # size. So I'm just setting the minimum size to the best
        # size.
        log.debug('Setting toolbar sizes: min {}, best {}'.format(
            (ttlWidth, minHeight), (ttlWidth, minHeight)))
        
        self.SetMinSize((   ttlWidth, minHeight))
        self.SetMaxSize((   ttlWidth, minHeight))
        self.CacheBestSize((ttlWidth, minHeight))
        
        return (ttlWidth, minHeight)
        

    
    def ClearTools(
            self,
            destroy=False,
            startIdx=None,
            endIdx=None,
            postevent=True):
 
        if len(self.__tools) == 0:
            return

        if startIdx is None: startIdx = 0
        if endIdx   is None: endIdx   = len(self.__tools)

        for i in range(startIdx, endIdx):
            tool = self.__tools[i]

            self.__sizer.Detach(tool)
            
            if destroy:
                tool.Destroy()

        self.__tools[startIdx:endIdx] = []

        self.InvalidateBestSize()
        self.Layout()

        if postevent:
            wx.PostEvent(self, ToolBarEvent())
