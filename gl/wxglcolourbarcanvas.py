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
import wx.glcanvas as wxgl

import fsl.fsleyes.gl                 as fslgl
import fsl.fsleyes.gl.colourbarcanvas as cbarcanvas

 
class WXGLColourBarCanvas(cbarcanvas.ColourBarCanvas,
                          fslgl.WXGLCanvasTarget,
                          wxgl.GLCanvas):
    """The ``WXGLColourBarCanvas`` is a :class:`.ColourBarCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.ColourBarCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLColourBarCanvas``.

    .. note:: The ``WXGLColourBarCanvas`` assumes the existence of the
              :meth:`.ColourBarCanvas._genColourBarTexture` method.
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
