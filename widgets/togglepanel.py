#!/usr/bin/env python
#
# togglepanel.py - A panel which contains a button, and some content.
# Pushing the button toggles the visibility of the content.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TogglePanel` class, which is a
:class:`wx.Panel` that contains a button and some content. Pushing
the button toggles the visibility of the content.
"""


import wx
import wx.lib.newevent as wxevent


_TogglePanelEvent, _EVT_TOGGLEPANEL_EVENT = wxevent.NewEvent()


EVT_TOGGLEPANEL_EVENT = _EVT_TOGGLEPANEL_EVENT
"""Identifier for the :data:`TogglePanelEvent` event."""


TogglePanelEvent = _TogglePanelEvent
"""Event emitted when the toggle button is pushed. Contains the
following attributes:

  - ``newState``: The new visibility state of the toggle panel - ``True``
                  corresponds to visible, ``False`` to invisible.
"""


class TogglePanel(wx.Panel):
    """A  :class:`TogglePanel` is a :class:`wx.Panel` that contains
    a button and some content.

    Pushing the button toggles the visibility of the content.
    
    All of the content should be added to the :class:`wx.Panel` which
    is returned by the :meth:`getContentPanel` method.
    """

    def __init__(self,
                 parent,
                 toggleSide=wx.TOP,
                 initialState=True,
                 label=None):
        """Create a :class:`TogglePanel`.

        :arg parent:       The :mod:`wx` parent object.

        :arg toggleSide:   Which side to place the toggle button. Must be one
                           of :attr:`wx.TOP`, :attr:`wx.BOTTOM`,
                           :attr:`wx.LEFT`, or :attr:`wx.RIGHT`.

        :arg initialState: Initial state for the panel content - visible
                           (``True``) or hidden (``False``).

        :arg label:        A label to be displayed on the toggle button.
        """

        wx.Panel.__init__(self, parent)

        self.__contentPanel = wx.Panel(self)

        if toggleSide in (wx.TOP, wx.BOTTOM):
            self.__sizer = wx.BoxSizer(wx.VERTICAL)
            
        elif toggleSide in (wx.LEFT, wx.RIGHT):
            self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
            
        else:
            raise ValueError('toggleSide must be one of wx.TOP, '
                             'wx.BOTTOM, wx.LEFT or wx.RIGHT')

        self.__toggleButton = wx.Button(self, style=wx.BU_EXACTFIT)
        self.__toggleButton.SetFont(self.__toggleButton.GetFont().Smaller())

        if   toggleSide == wx.TOP:    hideLabel = u'\u25B2' 
        elif toggleSide == wx.BOTTOM: hideLabel = u'\u25BC' 
        elif toggleSide == wx.LEFT:   hideLabel = u'\u25C0' 
        elif toggleSide == wx.RIGHT:  hideLabel = u'\u25B6'
        
        if   toggleSide == wx.TOP:    showLabel = u'\u25BC' 
        elif toggleSide == wx.BOTTOM: showLabel = u'\u25B2' 
        elif toggleSide == wx.LEFT:   showLabel = u'\u25B6' 
        elif toggleSide == wx.RIGHT:  showLabel = u'\u25C0' 

        self.__showLabel = showLabel
        self.__hideLabel = hideLabel

        self.__toggleButton.SetLabel(self.__hideLabel)

        if toggleSide in (wx.TOP, wx.LEFT):
            self.__sizer.Add(self.__toggleButton, flag=wx.EXPAND)
            self.__sizer.Add(self.__contentPanel, flag=wx.EXPAND, proportion=1)
            
        elif toggleSide in (wx.BOTTOM, wx.RIGHT):
            self.__sizer.Add(self.__contentPanel, flag=wx.EXPAND, proportion=1)
            self.__sizer.Add(self.__toggleButton, flag=wx.EXPAND)

        self.__toggleButton.Bind(wx.EVT_BUTTON, self.toggle)

        self.SetSizer(self.__sizer)

        if not initialState:
            self.toggle()


    def toggle(self, ev=None):
        """Toggles visibility of the panel content."""
        
        isShown = self.__sizer.IsShown(self.__contentPanel)

        self.__sizer.Show(self.__contentPanel, not isShown)
        
        if isShown: self.__toggleButton.SetLabel(self.__showLabel)
        else:       self.__toggleButton.SetLabel(self.__hideLabel)

        wx.PostEvent(self, TogglePanelEvent(newState=not isShown))

        self.Layout()
        self.__contentPanel.Layout()

    
    def getContentPanel(self):
        """Returns the :class:`wx.Panel` to which all content should be
        added.
        """
        return self.__contentPanel
