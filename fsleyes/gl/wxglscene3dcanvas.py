#!/usr/bin/env python
#
# wxglscene3dcanvas.py - The WXGLScene3DCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLScene3DCanvas` class, which is a
:class:`.Scene3DCanvas` for use in a :mod:`wx` application.
"""


import six

import wx.glcanvas as wxgl

import fsleyes.gl               as fslgl
import fsleyes.gl.scene3dcanvas as scene3dcanvas


class WXGLScene3DCanvas(six.with_metaclass(fslgl.WXGLMetaClass,
                                           scene3dcanvas.Scene3DCanvas,
                                           fslgl.WXGLCanvasTarget,
                                           wxgl.GLCanvas)):
    """The ``WXGLScene3DCanvas`` is a :class:`.Scene3DCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.Scene3DCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLScene3DCanvas``.
    """


    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``WXGLScene3DCanvas``. See :meth:`.Scene3DCanvas.__init__`
        for details on the arguments.
        """
        attrs = fslgl.WXGLCanvasTarget.displayAttribues()

        wxgl.GLCanvas              .__init__(self, parent, **attrs)
        fslgl.WXGLCanvasTarget     .__init__(self)
        scene3dcanvas.Scene3DCanvas.__init__(self, overlayList, displayCtx)


    def destroy(self):
        """Must be called when this ``WXGLScene3DCanvas`` is no longer needed.
        Clears some event listeners and calls the base class ``destroy``
        method.
        """
        scene3dcanvas.Scene3DCanvas.destroy(self)
        fslgl.WXGLCanvasTarget     .destroy(self)
