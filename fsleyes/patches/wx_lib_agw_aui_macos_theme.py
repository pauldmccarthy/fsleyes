#!/usr/bin/env python
#
# Monkey patch the changes proposed in
#
# https://github.com/wxWidgets/Phoenix/pull/2018/files
#
# which have not yet been merged into upstream wxpython.
#


import wx
import wx.lib.agw.aui.aui_utilities as aui_utilities
import wx.lib.agw.aui.dockart       as dockart
import wx.lib.agw.aui.tabart        as tabart


def aui_utilities_GetBaseColour():
    base_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)

    # the base_colour is too pale to use as our base colour,
    # so darken it a bit
    if ((255-base_colour.Red()) +
        (255-base_colour.Green()) +
        (255-base_colour.Blue()) < 60):

        base_colour = aui_utilities.StepColour(base_colour, 92)

    return base_colour


def dockart_AuiDefaultDockArt_Init(self):
    def Init(self):
        """ Initializes the dock art. """

        self.SetDefaultColours()

        isMac = wx.Platform == "__WXMAC__"

        if isMac:
            self._active_caption_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        else:
            self._active_caption_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION)

        self._active_caption_gradient_colour = LightContrastColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self._active_caption_text_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        self._inactive_caption_text_colour =  wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)


def tabart_AuiDefaultTabArt___init__(self):

    self._normal_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    self._selected_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    self._selected_font.SetWeight(wx.FONTWEIGHT_BOLD)
    self._measuring_font = self._selected_font

    self._fixed_tab_width = 100
    self._tab_ctrl_height = 0
    self._buttonRect = wx.Rect()

    self.SetDefaultColours()

    active_colour, disabled_colour = wx.BLACK, wx.Colour(128, 128, 128)

    if wx.Platform == "__WXMAC__":
        bmp_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DDKSHADOW)
        self._active_close_bmp = DrawMACCloseButton(bmp_colour)
        self._disabled_close_bmp = DrawMACCloseButton(disabled_colour)
    else:
        self._active_close_bmp = BitmapFromBits(nb_close_bits, 16, 16, active_colour)
        self._disabled_close_bmp = BitmapFromBits(nb_close_bits, 16, 16, disabled_colour)

    self._hover_close_bmp = self._active_close_bmp
    self._pressed_close_bmp = self._active_close_bmp

    self._active_left_bmp = BitmapFromBits(nb_left_bits, 16, 16, active_colour)
    self._disabled_left_bmp = BitmapFromBits(nb_left_bits, 16, 16, disabled_colour)

    self._active_right_bmp = BitmapFromBits(nb_right_bits, 16, 16, active_colour)
    self._disabled_right_bmp = BitmapFromBits(nb_right_bits, 16, 16, disabled_colour)

    self._active_windowlist_bmp = BitmapFromBits(nb_list_bits, 16, 16, active_colour)
    self._disabled_windowlist_bmp = BitmapFromBits(nb_list_bits, 16, 16, disabled_colour)

    self._focusPen = wx.Pen(active_colour, 1, wx.PENSTYLE_USER_DASH)
    self._focusPen.SetDashes([1, 1])
    self._focusPen.SetCap(wx.CAP_BUTT)


aui_utilites.CARBON              = False
aui_utilites.GetBaseColour       = aui_utilities_GetBaseColour
dockart.AuiDefaultDockArt.Init   = dockart_AuiDefaultDockArt_Init
tabart.CARBON                    = False
tabart.AuiDefaultTabArt.__init__ = tabart_AuiDefaultTabArt___init__
