#!/usr/bin/env python
#
# scene3dpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import logging

import wx

import fsleyes.displaycontext.scene3dopts as scene3dopts
import fsleyes.gl.wxglscene3dcanvas       as scene3dcanvas
from . import canvaspanel


log = logging.getLogger(__name__)


class Scene3DPanel(canvaspanel.CanvasPanel):

    def __init__(self, parent, overlayList, displayCtx, frame):

        sceneOpts = scene3dopts.Scene3DOpts()

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         sceneOpts)

        contentPanel = self.getContentPanel()

        self.__canvas = scene3dcanvas.WXGLScene3DCanvas(contentPanel,
                                                        overlayList,
                                                        displayCtx)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.__canvas, flag=wx.EXPAND, proportion=1)
        contentPanel.SetSizer(sizer)

        self.centrePanelLayout()
        self.initProfile()


    def getGLCanvases(self):
        """Returns all of the :class:`.SliceCanvas` instances contained
        within this ``Scene3DPanel``.
        """
        return [self.__canvas]
