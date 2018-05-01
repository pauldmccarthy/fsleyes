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

    import fsleyes.icons as icons

    # Get the file name
    fname = icons.findImageFile('gear24')

    # Get a wx.Bitmap containing the gear icon
    gearBmp = icons.loadBitmap('gear24')
"""


import os.path as op

import wx

import fsleyes


BUM_MODE = False
"""If ``True``, all icons are made to look like bums. """


def getIconDir():
    """Returns the directory which contains all of the icons used in
     *FSLeyes*.
    """
    return op.join(fsleyes.assetDir, 'assets', 'icons')


def findImageFile(iconId):
    """Returns the full path to the icon with the given ``iconId``.
    """
    if BUM_MODE and iconId[-2:] in ('16', '24'):
        size = iconId[-2:]
        if 'Highlight' in iconId:
            iconId = 'coronalBumSliceHighlight{}'.format(size)
        else:
            iconId = 'coronalBumSlice{}'.format(size)
    return op.join(getIconDir(), '{}.png'.format(iconId))


def loadBitmap(iconId):
    """Loads and returns a :class:`wx.Bitmap` containing the specified
    ``iconId``.
    """

    filename = findImageFile(iconId)
    bmp      = wx.Bitmap(filename, wx.BITMAP_TYPE_PNG)

    return bmp
