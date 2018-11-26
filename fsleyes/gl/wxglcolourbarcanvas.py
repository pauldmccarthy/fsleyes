#!/usr/bin/env python
#
# wxglcolourbarcanvas.py - The WXGLColourBarCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLColourBarCanvas` class, which is a
:class:`.ColourBarCanvas` for use in a :mod:`wx` application.
"""


import six

import wx
import wx.glcanvas as wxgl

import fsleyes.gl                 as fslgl
import fsleyes.gl.colourbarcanvas as cbarcanvas


class WXGLColourBarCanvas(six.with_metaclass(fslgl.WXGLMetaClass,
                                             cbarcanvas.ColourBarCanvas,
                                             fslgl.WXGLCanvasTarget,
                                             wxgl.GLCanvas)):
    """The ``WXGLColourBarCanvas`` is a :class:`.ColourBarCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.ColourBarCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLColourBarCanvas``.

    .. note:: The ``WXGLColourBarCanvas`` assumes the existence of the
              :meth:`.ColourBarCanvas.updateColourBarTexture` method.
    """
    def __init__(self, parent, overlayList, displayCtx):

        wxgl.GLCanvas             .__init__(self, parent)
        fslgl.WXGLCanvasTarget    .__init__(self)
        cbarcanvas.ColourBarCanvas.__init__(self, overlayList, displayCtx)

        def onsize(ev):
            self.updateColourBarTexture()
            ev.Skip()

        self.Bind(wx.EVT_SIZE, onsize)
