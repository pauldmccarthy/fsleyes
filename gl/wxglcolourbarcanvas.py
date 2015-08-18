#!/usr/bin/env python
#
# wxglcolourbarcanvas.py - Provides the WXGLColourBarCanvas, for displaying
# a colour bar on a wx.glcanvas.GLCanvas canvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLColourBarCanvas`, for displaying a
:class:`.ColourBarCanvas` on a :class:`wx.glcanvas.GLCanvas`.
"""

import logging
log = logging.getLogger(__name__)


import wx
import wx.glcanvas as wxgl

import fsl.fsleyes.gl                 as fslgl
import fsl.fsleyes.gl.colourbarcanvas as cbarcanvas

 
class WXGLColourBarCanvas(cbarcanvas.ColourBarCanvas,
                          fslgl.WXGLCanvasTarget,
                          wxgl.GLCanvas):
    """A :class:`.ColourBarCanvas` which is also a
    :class:`wx.glcanvas.GLCanvas`, for on screen rendering of colour bars.
    """
    def __init__(self, parent):
        
        wxgl.GLCanvas             .__init__(self, parent)
        cbarcanvas.ColourBarCanvas.__init__(self)
        fslgl.WXGLCanvasTarget    .__init__(self)

        def onsize(ev):
            self._genColourBarTexture()
            self.Refresh()
            ev.Skip()

        self.Bind(wx.EVT_SIZE, onsize)

ColourBarCanvas = WXGLColourBarCanvas
