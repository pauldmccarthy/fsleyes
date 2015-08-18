#!/usr/bin/env python
#
# textpanel.py - A panel for displaying horizontal or vertical text.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TextPanel` class, for displaying 
some text, oriented either horizontally or vertically.
"""

import logging
log = logging.getLogger(__name__)

import wx

class TextPanel(wx.Panel):
    """A :class:`wx.Panel` which may be used to display a string of
    text, oriented either horizotnally or vertically.
    """

    def __init__(self, parent, text=None, orient='horizontal'):
        wx.Panel.__init__(self, parent)

        self.Bind(wx.EVT_PAINT, self.Draw)
        self.Bind(wx.EVT_SIZE,  self._onSize)

        self._text = text
        self.SetOrient(orient)


    def SetOrient(self, orient):

        if orient not in ('horizontal', 'vertical'):
            raise RuntimeError('TextPanel orient must be '
                               'horizontal or vertical')
        
        self._orient = orient

        # trigger re-calculation of
        # text extents and a refresh
        self.SetText(self._text)

        
    def SetText(self, text):
        
        dc = wx.ClientDC(self)

        self._text = text

        if text is None:
            self.SetMinSize((0, 0))
            return

        width, height = dc.GetTextExtent(text)

        if self._orient == 'vertical':
            width, height = height, width

        self._textExtent = (width, height)

        self.SetMinSize((width, height))

        self.Refresh()


    def _onSize(self, ev):
        self.Refresh()
        ev.Skip()

        
    def Draw(self, ev=None):

        self.ClearBackground()

        if self._text is None or self._text == '':
            return

        if ev is None: dc = wx.ClientDC(self)
        else:          dc = wx.PaintDC( self)

        if not dc.IsOk():
            return

        paneW, paneH = dc.GetSize().Get()
        textW, textH = self._textExtent

        x = (paneW - textW) / 2.0
        y = (paneH - textH) / 2.0

        if self._orient == 'vertical':
            dc.DrawRotatedText(self._text, x, paneH - y, 90)
        else:
            dc.DrawText(self._text, x, y)
