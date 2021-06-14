#!/usr/bin/env python
#
# wxglcolourbarcanvas.py - The WXGLColourBarCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLColourBarCanvas` class, which is a
:class:`.ColourBarCanvas` for use in a :mod:`wx` application.
"""


import wx
import wx.siplib   as sip
import wx.glcanvas as wxgl

import fsleyes.gl                 as fslgl
import fsleyes.gl.colourbarcanvas as cbarcanvas


class WXGLColourBarCanvas(cbarcanvas.ColourBarCanvas,
                          fslgl.WXGLCanvasTarget,
                          wxgl.GLCanvas):
    """The ``WXGLColourBarCanvas`` is a :class:`.ColourBarCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.ColourBarCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLColourBarCanvas``.

    .. note:: The ``WXGLColourBarCanvas`` assumes the existence of the
              :meth:`.ColourBarCanvas.updateColourBarTexture` method.
    """

    __metaclass__ = sip.wrappertype

    def __init__(self, parent, overlayList, displayCtx):

        attrs = fslgl.WXGLCanvasTarget.displayAttributes()

        wxgl.GLCanvas             .__init__(self, parent, **attrs)
        fslgl.WXGLCanvasTarget    .__init__(self)
        cbarcanvas.ColourBarCanvas.__init__(self, overlayList, displayCtx)

        def onsize(ev):
            self.updateColourBarTexture()
            ev.Skip()

        self.Bind(wx.EVT_SIZE, onsize)


    def destroy(self):
        """Must be called when this ``WXGLColourBarCanvas`` is no longer
        needed. Clears some event listeners and calls the base class
        ``destroy`` method.
        """
        self.Unbind(wx.EVT_SIZE)

        cbarcanvas.ColourBarCanvas.destroy(self)
        fslgl.WXGLCanvasTarget    .destroy(self)
