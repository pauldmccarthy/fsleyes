#!/usr/bin/env python
#
# wxgllightboxcanvas.py - A wx.glcanvas.GLCanvas LightBoxCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLLightBoxCanvas`, which is both a
:class:`.LightBoxCanvas`, and a :class:`wx.glcanvas.GLCanvas`.
"""


import wx
import wx.glcanvas              as wxgl

import lightboxcanvas           as lightboxcanvas
import fsl.fsleyes.gl           as fslgl


class WXGLLightBoxCanvas(lightboxcanvas.LightBoxCanvas,
                         wxgl.GLCanvas,
                         fslgl.WXGLCanvasTarget):
    """A :class:`wx.glcanvas.GLCanvas` and a :class:`.SliceCanvas`, for 
    on-screen interactive 2D slice rendering from a collection of 3D
    overlays.
    """

    def __init__(self, parent, overlayList, displayCtx, zax=0):
        """Configures a few event handlers for cleaning up property
        listeners when the canvas is destroyed, and for redrawing on
        paint/resize events.
        """

        wxgl.GLCanvas                .__init__(self, parent)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)
        fslgl.WXGLCanvasTarget       .__init__(self)

        # When the canvas is resized, we have to update
        # the display bounds to preserve the aspect ratio
        def onResize(ev):
            self._updateDisplayBounds()
            ev.Skip()
        self.Bind(wx.EVT_SIZE, onResize)

# A convenient alias
LightBoxCanvas = WXGLLightBoxCanvas
