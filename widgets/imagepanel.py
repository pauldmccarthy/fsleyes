#!/usr/bin/env python
#
# imagepanel.py - A panel for displaying a wx.Image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImagePanel` class, for displaying a
:class:`wx.Image`.
"""

import logging

import wx


log = logging.getLogger(__name__)


class ImagePanel(wx.PyPanel):
    """A :class:`wx.PyPanel` which may be used to display a resizeable
    :class:`wx.Image`. The image is scaled to the size of the panel.
    """

    def __init__(self, parent, image=None):
        """Create an ``ImagePanel``.

        If the ``image`` is not passed in here, it can be set later with the
        :meth:`SetImage` method.

        :arg parent: The :mod:`wx` parent object.

        :arg image:  The :class:`wx.Image` object to display.
        """

        wx.PyPanel.__init__(self, parent)

        self.Bind(wx.EVT_PAINT, self.Draw)
        self.Bind(wx.EVT_SIZE,  self.__onSize)

        self.SetImage(image)


    def SetImage(self, image):
        """Set the image that is displayed on this ``ImagePanel``.

        :arg image: The :class:`wx.Image` object to display.
        """
        self.__image = image
        self.Refresh()

        
    def __onSize(self, ev):
        """Redraw this panel when it is sized, so the image is scaled
        appropriately - see the :meth:`Draw` method.
        """
        self.Refresh()
        ev.Skip()


    def DoGetBestSize(self):
        """Returns the size of the image being displayed.
        """

        if self.__image is None: return (0, 0)
        else:                    return self.__image.GetSize()
        
        
    def Draw(self, ev=None):
        """Draws this ``ImagePanel``. The image is scaled to the current panel
        size.
        """

        self.ClearBackground()

        if self.__image is None:
            return

        if ev is None: dc = wx.ClientDC(self)
        else:          dc = wx.PaintDC( self)

        if not dc.IsOk():
            return 
        
        width, height = dc.GetSize().Get()

        if width == 0 or height == 0:
            return

        bitmap = wx.BitmapFromImage(self.__image.Scale(width, height))
        
        dc.DrawBitmap(bitmap, 0, 0, False)
