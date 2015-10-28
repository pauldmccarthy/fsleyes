#!/usr/bin/env python
#
# icons.py - Application/button icons for FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a couple of convenience functions for looking up
*FSLeyes* icon images.


Icons can be looked up by their ID, which  is simply the icon file base name.
For exmaple, the bitmap for an icon called ``gear24.png``  can be retreived
like so::

    import fsl.fsleyes.icons as icons

    # Get the file name
    fname = icons.findImageFile('gear24')

    # Get a wx.Bitmap containing the gear icon
    gearBmp = icons.loadBitmap('gear24')
"""


import os.path as op

import wx


_ICON_PATH = op.join(op.dirname(__file__), 'icons')
"""The directory which contains all of the icons used in *FSLeyes*. """


def findImageFile(iconId):
    """Returns the full path to the icon with the given ``iconId``.
    """
    return op.join(_ICON_PATH, '{}.png'.format(iconId))


def loadBitmap(iconId):
    """Loads and returns a :class:`wx.Bitmap` containing the specified
    ``iconId``.
    """

    filename = findImageFile(iconId)
    bmp = wx.EmptyBitmap(1, 1)
    bmp.LoadFile(filename, wx.BITMAP_TYPE_PNG)

    return bmp
