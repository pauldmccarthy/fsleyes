#!/usr/bin/env python
#
# wxglslicecanvas.py - The WXGLSliceCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLSliceCanvas` class, which is a
:class:`.SliceCanvas` for use in a :mod:`wx` application.
"""


import wx
import wx.glcanvas    as wxgl

import slicecanvas    as slicecanvas
import fsl.fsleyes.gl as fslgl


class WXGLSliceCanvas(slicecanvas.SliceCanvas,
                      wxgl.GLCanvas,
                      fslgl.WXGLCanvasTarget):
    """The ``WXGLSliceCanvas`` is a :class:`.SliceCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.SliceCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLSliceCanvas``.

    .. note:: The ``WXGLSliceCanvas`` assumes the existence of the
              :meth:`.SliceCanvas._updateDisplayBounds` method.
    """

    def __init__(self, parent, overlayList, displayCtx, zax=0):
        """Create a ``WXGLSliceCanvas``. See :meth:`.SliceCanvas.__init__` for
        details on the arguments.
        """

        wxgl.GLCanvas          .__init__(self, parent)
        slicecanvas.SliceCanvas.__init__(self, overlayList, displayCtx, zax)
        fslgl.WXGLCanvasTarget .__init__(self)

        self.Bind(wx.EVT_SIZE, self.__onResize)


    def __onResize(self, ev):
        """Called on ``wx.EVT_SIZE`` events, when the canvas is resized. When
        the canvas is resized, we have to update the display bounds to preserve
        the aspect ratio.
        """
        self._updateDisplayBounds()
        ev.Skip()


    def Show(self, show):
        """Overrides ``GLCanvas.Show``. When running over SSH/X11, it doesn't
        seem to be possible to hide a ``GLCanvas`` - the most recent scene
        displayed on the canvas seems to persist, does not get overridden, and
        gets drawn on top of other things in the interface:

        .. image:: images/x11_slicecanvas_show_bug.png
           :scale: 50%
           :align: center

        This is not ideal, and I have no idea why it occurs. The only
        workaround that I've found to work is, instead of hiding the canvas,
        to set its size to 0. So this method does just that.
        """
        wxgl.GLCanvas.Show(self, show)
        if not show:
            self.SetMinSize((0, 0))
            self.SetMaxSize((0, 0))
            self.SetSize(   (0, 0))


    def Hide(self):
        """Overrides ``GLCanvas.Hide``. Calls :meth:`Show`. """
        self.Show(False)
