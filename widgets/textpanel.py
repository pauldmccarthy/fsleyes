#!/usr/bin/env python
#
# textpanel.py - A panel for displaying horizontal or vertical text.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TextPanel` class, for displaying 
some text, oriented either horizontally or vertically.
"""


import wx


class TextPanel(wx.PyPanel):
    """A :class:`wx.PyPanel` which may be used to display a string of
    text, oriented either horizotnally or vertically.
    """

    def __init__(self, parent, text=None, orient=wx.HORIZONTAL):
        """Create a ``TextPanel``.

        :arg parent: The :mod:`wx` parent object.

        :arg text:   The text to display. This can be changed via
                     :meth:`SetText`.

        :arg orient: Text orientation - either ``wx.HORIZONTAL`` (the
                     default) or ``wx.VERTICAL``. This can be changed
                     later via :meth:`SetOrient`.
        """
        wx.PyPanel.__init__(self, parent)

        self.Bind(wx.EVT_PAINT, self.Draw)
        self.Bind(wx.EVT_SIZE,  self.__onSize)

        self.__text = text
        self.SetOrient(orient)


    def SetOrient(self, orient):
        """Sets the orientatino of the text on this ``TextPanel``.

        :arg orient: Either ``wx.HORIZONTAL`` or ``wx.VERTICAL``.
        """

        if orient not in (wx.HORIZONTAL, wx.VERTICAL):
            raise ValueError('TextPanel orient must be '
                             'wx.HORIZONTAL or wx.VERTICAL')
        
        self.__orient = orient

        # trigger re-calculation of
        # text extents and a refresh
        self.SetText(self.__text)

        
    def SetText(self, text):
        """Sets the text shown on this ``TextPanel``."""
        
        dc = wx.ClientDC(self)

        self.__text = text

        if text is None:
            self.SetMinSize((0, 0))
            return

        width, height = dc.GetTextExtent(text)

        if self._orient == 'vertical':
            width, height = height, width

        self.__textExtent = (width, height)

        self.SetMinSize((width, height))

        self.Refresh()


    def __onSize(self, ev):
        """Called when this ``TextPanel`` is resized. Triggers a refresh. """
        self.Refresh()
        ev.Skip()

        
    def Draw(self, ev=None):
        """Draws this ``TextPanel``. """

        self.ClearBackground()

        if self.__text is None or self.__text == '':
            return

        if ev is None: dc = wx.ClientDC(self)
        else:          dc = wx.PaintDC( self)

        if not dc.IsOk():
            return

        paneW, paneH = dc.GetSize().Get()
        textW, textH = self.__textExtent

        x = (paneW - textW) / 2.0
        y = (paneH - textH) / 2.0

        if self._orient == 'vertical':
            dc.DrawRotatedText(self.__text, x, paneH - y, 90)
        else:
            dc.DrawText(self.__text, x, y)
