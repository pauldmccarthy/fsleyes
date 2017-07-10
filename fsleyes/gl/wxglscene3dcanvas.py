#!/usr/bin/env python
#
# wxglscene3dcanvas.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import six

import wx
import wx.glcanvas as wxgl


import fsleyes.gl               as fslgl
import fsleyes.gl.scene3dcanvas as scene3dcanvas


class WXGLScene3DCanvas(six.with_metaclass(fslgl.WXGLMetaClass,
                                           scene3dcanvas.Scene3DCanvas,
                                           fslgl.WXGLCanvasTarget,
                                           wxgl.GLCanvas)):

    def __init__(self, parent, overlayList, displayCtx):

        wxgl.GLCanvas              .__init__(self, parent)
        fslgl.WXGLCanvasTarget     .__init__(self)
        scene3dcanvas.Scene3DCanvas.__init__(self, overlayList, displayCtx)
