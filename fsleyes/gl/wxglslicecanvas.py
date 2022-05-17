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
import wx.siplib   as sip
import wx.glcanvas as wxgl

import fsleyes_widgets as     fwidgets
import fsleyes_props   as     props

import fsleyes.gl      as     fslgl
from   .               import slicecanvas


class WXGLSliceCanvas(slicecanvas.SliceCanvas,
                      fslgl.WXGLCanvasTarget,
                      wxgl.GLCanvas):
    """The ``WXGLSliceCanvas`` is a :class:`.SliceCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.SliceCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLSliceCanvas``.

    .. note:: The ``WXGLSliceCanvas`` assumes the existence of the
              :meth:`.SliceCanvas._updateDisplayBounds` method.
    """

    __metaclass__ = sip.wrappertype

    def __init__(self, parent, overlayList, displayCtx, zax=0):
        """Create a ``WXGLSliceCanvas``. See :meth:`.SliceCanvas.__init__` for
        details on the arguments.
        """

        attrs = fslgl.WXGLCanvasTarget.displayAttributes()

        wxgl.GLCanvas          .__init__(self, parent, **attrs)
        fslgl.WXGLCanvasTarget .__init__(self)
        slicecanvas.SliceCanvas.__init__(self, overlayList, displayCtx, zax)

        self.Bind(wx.EVT_SIZE, self.__onResize)


    def destroy(self):
        """Must be called when this ``WXGLSliceCanvas`` is no longer needed.
        Clears some event listeners and calls the base class ``destroy``
        method.
        """
        self.Unbind(wx.EVT_SIZE)
        slicecanvas.SliceCanvas.destroy(self)
        fslgl.WXGLCanvasTarget .destroy(self)


    def __onResize(self, ev):
        """Called on ``wx.EVT_SIZE`` events, when the canvas is resized. When
        the canvas is resized, we have to update the display bounds to preserve
        the aspect ratio.
        """
        ev.Skip()

        with props.skip(self.opts, 'displayBounds', self.name):
            centre = self.getDisplayCentre()
            self._updateDisplayBounds()
            self.centreDisplayAt(*centre)
