#!/usr/bin/env python
#
# wxglslicecanvas.py - A SliceCanvas which is rendered using a
# wx.glcanvas.GLCanvas panel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :class:`WXGLSliceCanvas` class is both a :class:`.SliceCanvas` and a
:class:`wx.glcanvas.GLCanvas` panel.

It is the main class used for on-screen orthographic rendering of 3D image
data (although most of the functionality is provided by the
:class:`.SliceCanvas` class).
"""


import wx
import wx.glcanvas    as wxgl

import slicecanvas    as slicecanvas
import fsl.fsleyes.gl as fslgl


class WXGLSliceCanvas(slicecanvas.SliceCanvas,
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

        wxgl.GLCanvas          .__init__(self, parent)
        slicecanvas.SliceCanvas.__init__(self, overlayList, displayCtx, zax)
        fslgl.WXGLCanvasTarget .__init__(self)

        # When the canvas is resized, we have to update
        # the display bounds to preserve the aspect ratio
        def onResize(ev):
            self._updateDisplayBounds()
            ev.Skip()
        self.Bind(wx.EVT_SIZE, onResize)
