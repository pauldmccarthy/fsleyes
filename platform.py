#!/usr/bin/env python
#
# platform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os

haveGui    = False
wxFlavour  = None
wxPlatform = None


WX_PYTHON  = 1
WX_PHOENIX = 2

WX_MAC = 1
WX_GTK = 2

class Platform(object):
    def __init__(self):

        self.haveGui    = False
        self.wxFlavour  = None
        self.wxPlatform = None

        try:
            import wx
            self.haveGui = True

        except ImportError:
            pass

        if self.haveGui:
            if 'phoenix' in wx.PlatformInformation:
                self.wxFlavour = WX_PHOENIX
                
            if 'MAC' in wx.Platform:
                self.wxPlatform = WX_MAC

        # TODO Make Platform a notifier, so
        #      things can register to listen
        #      for changes to $FSLDIR
        self.fsldir = os.environ['FSLDIR']
