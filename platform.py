#!/usr/bin/env python
#
# platform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

haveGui    = False
wxFlavour  = None
wxPlatform = None


WX_PYTHON  = 1
WX_PHOENIX = 2

WX_MAC = 1
WX_GTK = 2


try:
    import wx
    haveGui = True

except ImportError:
    haveGui = False


if 'phoenix' in wx.PlatformInformation: wxFlavour = WX_PHOENIX
else:                                   wxFlavour = WX_PYTHON


if   'MAC' in wx.Platform: wxPlatform = WX_MAC
elif 'GTK' in wx.Platform: wxPlatform = WX_GTK
