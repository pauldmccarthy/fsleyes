#!/usr/bin/env python
#
# wxgllightboxcanvas.py - THe  WXGLLightBoxCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLSliceCanvas` class, which is a
:class:`.SliceCanvas` for use in a :mod:`wx` application.
"""
"""This module provides the :class:`WXGLLightBoxCanvas`, which is a
:class:`.LightBoxCanvas` for use in a :mod:`wx` application.
"""


import six

import wx
import wx.glcanvas as wxgl

import fsleyes.gl  as fslgl
from . import         lightboxcanvas


class WXGLLightBoxCanvas(six.with_metaclass(fslgl.WXGLMetaClass,
                                            lightboxcanvas.LightBoxCanvas,
                                            fslgl.WXGLCanvasTarget,
                                            wxgl.GLCanvas)):
    """The ``WXGLLightBoxCanvas`` is a :class:`.LightBoxCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.LightBoxCanvas` in your :mod:`wx` application,
    then you should use a ``WXGLLightBoxCanvas``.

    .. note:: The ``WXGLLightBoxCanvas`` assumes the existence of the
              :meth:`.LightBoxCanvas._updateDisplayBounds` method.
    """


    def __init__(self, parent, overlayList, displayCtx, zax=0):
        """Create a ``WXGLLightBoxCanvas``. See
        :meth:`.LightBoxCanvas.__init__` for details on the arguments.
        """

        attrs = fslgl.WXGLCanvasTarget.displayAttribues()

        wxgl.GLCanvas                .__init__(self, parent, **attrs)
        fslgl.WXGLCanvasTarget       .__init__(self)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)

        # When the canvas is resized, we have to update
        # the display bounds to preserve the aspect ratio
        def onResize(ev):
            self._updateDisplayBounds()
            ev.Skip()
        self.Bind(wx.EVT_SIZE, onResize)


    def destroy(self):
        """Must be called when this ``WXGLLightBoxCanvas`` is no longer
        needed. Clears some event listeners and calls the base class
        ``destroy`` method.
        """
        self.Unbind(wx.EVT_SIZE)
        lightboxcanvas.LightBoxCanvas.destroy(self)
        fslgl.WXGLCanvasTarget       .destroy(self)
