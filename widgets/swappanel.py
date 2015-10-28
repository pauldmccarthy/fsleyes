#!/usr/bin/env python
#
# swappanel.py - A wx.Panel which can contain many panels, but only displays
# one at a time.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SwapPanel` class, which is a
:class:`wx.PyPanel` that can contain many child panels, but only displays one
at a time.
"""


import wx


class SwapPanel(wx.PyPanel):
    """The ``SwapPanel`` is a panel which can contain many cvhild panels, but
    only displays one of them at a time. A button push allows the user to
    change the currently displayed child panel.
    """
    

    def __init__(self, parent, buttonSide=wx.TOP):
        """Create a ``SwapPanel``.

        :arg parent:     The :mod:`wx` parent object.

        :arg buttonSide: Which side to put the toggle button - one of
                         ``wx.TOP``, ``wx.BOTTOM``, ``wx.LEFT``, or
                         ``wx.RIGHT``.
        """

        wx.PyPanel.__init__(self, parent)
        
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
        """Add a new panel to this ``SwapPanel``.

        :arg panel: The panel.

        :arg label: An identifier label for the panel - this may be passed to
                    the :meth:`Remove` and :meth:`Show` methods to refer to 
                    this panel.
        """
        self.__panels.append(panel)
        self.__labels.append(label)

        panel.Reparent(self)

        if len(self.__panels) == 1:
            self.__Show(0)

        
    def Remove(self, label):
        """Remove the panel with the specified ``label``. """
        idx = self.__labels.index(label)

        self.__panels.pop(idx)
        self.__labels.pop(idx)


    def Show(self, label):
        """Show the panel with the specified ``label``. """
        idx = self.__labels.index(label)
        self.__Show(idx)


    def __Show(self, index):
        """Show the panel at the specified ``index``. """

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
        """Called when the toggle button is pushed. Shows the next panel."""
        self.__Show((self.__showing + 1) % len(self.__labels))
