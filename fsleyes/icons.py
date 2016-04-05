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


.. note:: The :func:`init` function must be called before any of the other
          functions in this module may be used.
"""


import os.path as op

import wx


_iconDir = None 
"""The directory which contains all of the icons used in *FSLeyes*. """


def init(iconDir=None):
    """Must be called before the other functions in this module. Sets
    the :data:`_iconDir`, the directory in which icon files may be found.
    Defaults to a directory called ``icons``, in the same directory as
    this module.
    """
    global _iconDir

    if iconDir is None: _iconDir = op.join(op.dirname(__file__), 'icons')
    else:               _iconDir = iconDir


def findImageFile(iconId):
    """Returns the full path to the icon with the given ``iconId``.
    """
    return op.join(_iconDir, '{}.png'.format(iconId))


def loadBitmap(iconId):
    """Loads and returns a :class:`wx.Bitmap` containing the specified
    ``iconId``.
    """

    filename = findImageFile(iconId)
    bmp      = wx.Bitmap(filename, wx.BITMAP_TYPE_PNG)

    return bmp
