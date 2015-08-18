#!/usr/bin/env python
#
# icons.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import os.path as op

import wx


_bitmapPath = op.join(op.dirname(__file__), 'icons')


def findImageFile(iconId):
    return op.join(_bitmapPath, '{}.png'.format(iconId))


def _resizeImage(image, size):
    
    w, h = image.GetSize().Get()

    if w >= h:
        h = size * h / float(w)
        w = size
    else:
        w = size * (w / float(h)) 
        h = size

    image.Rescale(w, h, wx.IMAGE_QUALITY_BICUBIC)
    return image


def loadBitmap(iconId):

    filename = findImageFile(iconId)
    bmp = wx.EmptyBitmap(1, 1)
    bmp.LoadFile(filename, wx.BITMAP_TYPE_PNG)

    return bmp
