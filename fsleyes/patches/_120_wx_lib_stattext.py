#!/usr/bin/env python
#
# Addresses https://github.com/wxWidgets/Phoenix/pull/2111
# in wxPython 4.1.x


import                    wx
import                    wx.lib.stattext
import fsleyes_widgets as fwidgets


if wx.Platform == "__WXMAC__":
    try:
        from Carbon.Appearance import kThemeBrushDialogBackgroundActive
    except ImportError:
        kThemeBrushDialogBackgroundActive = 1


def OnPaint(self, event):
    """
    Handles the ``wx.EVT_PAINT`` for :class:`GenStaticText`.

    :param `event`: a :class:`wx.PaintEvent` event to be processed.
    """

    if wx.lib.stattext.BUFFERED:
        dc = wx.BufferedPaintDC(self)
    else:
        dc = wx.PaintDC(self)
    width, height = self.GetClientSize()
    if not width or not height:
        return

    if wx.lib.stattext.BUFFERED:
        clr = self.GetBackgroundColour()
        if wx.Platform == "__WXMAC__" and clr == self.defBackClr:
            # if colour is still the default then use the theme's  background on Mac
            themeColour = wx.MacThemeColour(kThemeBrushDialogBackgroundActive)
            backBrush = wx.Brush(themeColour)
        else:
            backBrush = wx.Brush(clr, wx.BRUSHSTYLE_SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()

    if self.IsEnabled():
        dc.SetTextForeground(self.GetForegroundColour())
    else:
        dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

    dc.SetFont(self.GetFont())
    label = self.GetLabel()
    style = self.GetWindowStyleFlag()
    x = y = 0
    for line in label.split('\n'):
        if line == '':
            w, h = self.GetTextExtent('W')  # empty lines have height too
        else:
            w, h = self.GetTextExtent(line)
        if style & wx.ALIGN_RIGHT:
            x = width - w
        if style & wx.ALIGN_CENTER:
            x = (width - w)/2
        dc.DrawText(line, int(round(x)), int(round(y)))
        y += h


if fwidgets.wxVersion().startswith('4.1'):
    wx.lib.stattext.GenStaticText.OnPaint = OnPaint
