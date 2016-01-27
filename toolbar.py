#!/usr/bin/env python
#
# toolbar.py - FSLeyes toolbars
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLEyesToolBar` class, the base class
for all toolbars in *FSLeyes*.
"""

import logging

import wx
import wx.lib.newevent as wxevent

import numpy as np

import fsl.fsleyes.panel   as fslpanel
import fsl.fsleyes.icons   as icons


log = logging.getLogger(__name__)


class FSLEyesToolBar(fslpanel._FSLEyesPanel, wx.PyPanel):
    """Base class for all *FSLeyes* toolbars.

    The ``FSLEyesToolBar`` is a regular :class:`wx.PyPanel` which to which a
    group of *tools* can be added, where a tool may be any ``wx`` control.

    Tools can be added to a ``FSLEyesToolBar`` with the following methods:

      .. autosummary::
         :nosignatures:
    
         AddTool
         InsertTool
         InsertTools
         SetTools
         MakeLabelledTool
    
    
    When the horizontal size of a ``FSLEyesToolBar`` becomes too small to
    display all of its tools, the toolbar is compressed: some tools are
    hidden, and buttons are displayed on each end of the toolbar, allowing the
    user to scroll through the toolbar, to access the hidden tools. The user
    may also use the mouse wheel to scroll through the toolbar.

    A collapsed ``FSLEyesToolBar`` looks something like this:

    .. image:: images/fsleyestoolbar.png
       :scale: 50%
       :align: center
    """


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 height=32):
        """Create a ``FSLEyesToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`, containing all overlays
                          being displayed.
        
        :arg displayCtx:  A :class:`.DisplayContext`, which defines how the
                          overlays are to be displayed.
        
        :arg height:      Desired toolbar height in pixels. This value is used
                          to look up appropriately sized left/right arrow
                          icons.
                          
        :arg actionz:     A dictionary of actions passed through to the
                          :meth:`.ActionProvider.__init__`.
        """
        
        wx.PyPanel.__init__(self, parent)
        fslpanel._FSLEyesPanel.__init__(self, overlayList, displayCtx)

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


    def MakeLabelledTool(self, tool, labelText, labelSide=wx.TOP):
        """Creates a panel containing the given tool, and a label for the
        tool. The panel is returned, but is not added to this
        ``FSLEyesToolBar`` - you will have to do that yourself, e.g.::

            labelledTool = toolbar.MakeLabelledTool(tool, 'Label', wx.BOTTOM)
            toolbar.AddTool(labelledTool)

        :arg tool:      A :mod:`wx` control.
        
        :arg labelText: A label for the tool.
        
        :arg labelSide: Which side of the tool to put the label - ``wx.TOP``,
                        ``wx.BOTTOM``, ``wx.LEFT``, or ``wx.RIGHT``.
        """

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
        """Enables/disables all tools in this ``FSLEyesToolBar``.

        :arg args:   Passed to the ``Enable`` method of each tool.
        :arg kwargs: Passed to the ``Enable`` method of each tool.
        """
        wx.PyPanel.Enable(self, *args, **kwargs)
        for t in self.__tools:
            t.Enable(*args, **kwargs)

            
    def GetTools(self):
        """Returns a list containing all tools in this ``FSLEyesToolBar``. """
        return self.__tools[:]


    def GetToolCount(self):
        """Returns the number of tools in this ``FSLEyesToolBar``. """
        return len(self.__tools)


    def AddTool(self, tool):
        """Adds the given tool to this ``FSLEyesToolBar``. """
        self.InsertTool(tool)

        
    def InsertTools(self, tools, index=None):
        """Inserts the given sequence of tools into this ``FSLEyesToolBar``,
        at the specified index.

        :arg tools: A sequence of tools to add.

        :arg index: Insert the tools before this index.
        """

        for i, tool in enumerate(tools, index):
            self.InsertTool(tool, i, postevent=False)

        wx.PostEvent(self, ToolBarEvent())


    def SetTools(self, tools, destroy=False):
        """Replaces all of the existing tools in this ``FSLEyesToolBar``
        with the given sequence of tools.

        :arg tools:   Sequence of new tools to add.

        :arg destroy: If ``True`` all of the old tools are destroyed.
        """

        self.ClearTools(destroy, postevent=False)

        for tool in tools:
            self.InsertTool(tool, postevent=False)

        wx.PostEvent(self, ToolBarEvent())
        

    def InsertTool(self, tool, index=None, postevent=True):
        """Inserts the given tool into this ``FSLEyesToolBar``, at the
        specified index.

        :arg tool:      The tool to insert.

        :arg index:     Index to insert the tool.

        :arg postevent: If ``True``, a :data:`ToolBarEvent` will be generated.
                        Pass ``False`` to suppress this event.
        """

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
        """Calculates and returns the best size for this toolbar, simply the
        minimum size that will fit all tools.

        This method is called by :mod:`wx` when this toolbar is laid out.
        """

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
        """Removes all tools, or a range of tools, from this
        ``FSLEyesToolBar``.

        :arg destroy:   If ``True``, the removed tools are destroyed.
        
        :arg startIdx:  Start index of tools to remove. If not provided,
                        defaults to 0.
        
        :arg endIdx:    End index of tools to remove (exclusive). If not
                        provided, defaults to :meth:`GetToolCount()`.
        
        :arg postevent: If ``True``, a :data:`ToolBarEvent` will be
                        generated. Set to ``False`` to suppress the event.
        """
 
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
        

    def __onMouseWheel(self, ev):
        """Called when the mouse wheel is rotated on this ``FSLEyesToolBar``.

        Calls :meth:`__onLeftButton` or :meth:`__onRightButton`, depending
        on the rotation direction.
        """

        wheelDir = ev.GetWheelRotation()
        if   wheelDir < 0: self.__onRightButton()
        elif wheelDir > 0: self.__onLeftButton()


    def __onLeftButton(self, ev=None):
        """Called when the left toolbar button is pressed.

        If the toolbar is compressed, it is scrolled to the left.
        """

        self.__index -= 1

        if self.__index <= 0:
            self.__index = 0

        log.debug('Left button pushed - setting start '
                  'tool index to {}'.format(self.__index)) 

        self.__drawToolBar()

        
    def __onRightButton(self, ev=None):
        """Called when the right toolbar button is pressed.

        If the toolbar is compressed, it is scrolled to the right.
        """
        
        self.__index += 1

        if self.__index + self.__numVisible >= len(self.__tools):
            self.__index = len(self.__tools) - self.__numVisible

        log.debug('Right button pushed - setting start '
                  'tool index to {}'.format(self.__index))

        self.__drawToolBar()


    def __drawToolBar(self, *a):
        """Draws this ``FSLEyesToolBar``.

        If the toolbar is big enough, all tools are drawn. Otherwise, the
        method figures out out how many tools can be drawn, and which tools to
        draw, given the current size.
        """

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


_ToolBarEvent, _EVT_TOOLBAR_EVENT = wxevent.NewEvent()


EVT_TOOLBAR_EVENT = _EVT_TOOLBAR_EVENT
"""Identifier for the :data:`ToolBarEvent` event. """


ToolBarEvent = _ToolBarEvent
"""Event emitted when one or more tools is/are added/removed to/from a
:class:`FSLEyesToolBar`.
"""
