#!/usr/bin/env python
#
# scene3dpanel.py - The Scene3DPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import logging

import wx

import fsleyes.displaycontext.scene3dopts as scene3dopts
import fsleyes.gl.wxglscene3dcanvas       as scene3dcanvas
import fsleyes.actions                    as actions
from . import                                canvaspanel


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

        self.__canvas.bindProps('pos',          displayCtx, 'location')
        self.__canvas.bindProps('showCursor',   sceneOpts)
        self.__canvas.bindProps('cursorColour', sceneOpts)
        self.__canvas.bindProps('bgColour',     sceneOpts)
        self.__canvas.bindProps('showLegend',   sceneOpts)
        self.__canvas.bindProps('occlusion',    sceneOpts)
        self.__canvas.bindProps('light',        sceneOpts)
        self.__canvas.bindProps('lightPos',     sceneOpts)
        self.__canvas.bindProps('zoom',         sceneOpts)
        self.__canvas.bindProps('offset',       sceneOpts)
        self.__canvas.bindProps('rotation',     sceneOpts)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.__canvas, flag=wx.EXPAND, proportion=1)
        contentPanel.SetSizer(sizer)

        self.centrePanelLayout()
        self.initProfile()
        self.syncLocation = True


    def destroy(self):

        self.__canvas.destroy()
        self.__canvas = None
        canvaspanel.CanvasPanel.destroy(self)



    def getGLCanvases(self):
        """Returns all of the :class:`.SliceCanvas` instances contained
        within this ``Scene3DPanel``.
        """
        return [self.__canvas]


    def getActions(self):
        """
        """
        actionz = [self.screenshot,
                   self.showCommandLineArgs,
                   self.applyCommandLineArgs,
                   None,
                   self.toggleDisplaySync,
                   self.resetDisplay,
                   None,
                   self.toggleOverlayList,
                   self.toggleLocationPanel,
                   self.toggleOverlayInfo,
                   self.toggleDisplayPanel,
                   self.toggleCanvasSettingsPanel,
                   self.toggleAtlasPanel,
                   self.toggleDisplayToolBar,
                   self.toggleLookupTablePanel,
                   self.toggleClusterPanel,
                   self.toggleClassificationPanel,
                   self.removeAllPanels]

        def makeTuples(actionz):

            tuples = []

            for a in actionz:
                if isinstance(a, actions.Action):
                    tuples.append((a.__name__, a))

                elif isinstance(a, tuple):
                    tuples.append((a[0], makeTuples(a[1])))

                elif a is None:
                    tuples.append((None, None))

            return tuples

        return makeTuples(actionz)


    @actions.action
    def resetDisplay(self):
        """
        """
        self.getCurrentProfile().resetDisplay()
