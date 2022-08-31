#!/usr/bin/env python
#
# scene3dpanel.py - The Scene3DPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Scene3DPanel` class, a FSLeyes view which
draws the scene in 3D.
"""


import logging

import wx

import numpy as np

import fsl.transform.affine                as affine
import fsleyes.displaycontext.scene3dopts  as scene3dopts
import fsleyes.gl.wxglscene3dcanvas        as scene3dcanvas
import fsleyes.profiles.scene3dviewprofile as scene3dviewprofile
import fsleyes.actions                     as actions
from . import                                 canvaspanel


log = logging.getLogger(__name__)


class Scene3DPanel(canvaspanel.CanvasPanel):
    """The ``Scene3DPanel`` is a :class:`.CanvasPanel` which draws the
    contents of the :class:`.OverlayList` as a 3D scene.


    The ``Scene3DPanel`` uses a :class:`.Scene3DCanvas`, which manages all of
    the GL state and drawing logic. A :class:`.Scene3DViewProfile` instance
    is used to manage all of the user interaction logic.


    The scene properties are described and changed via a :class:`.Scene3DOpts`
    instance, accessible through the :meth:`.CanvasPanel.sceneOpts`
    property.
    """


    @staticmethod
    def defaultLayout():
        """Returns a list of control panel types to be added for the default
        3D panel layout.
        """
        return ['OverlayDisplayToolBar',
                'Scene3DToolBar',
                'OverlayListPanel',
                'LocationPanel']


    @staticmethod
    def controlOrder():
        """Returns a list of control panel names, specifying the order in
        which they should appear in the  FSLeyes ortho panel settings menu.
        """
        return ['OverlayListPanel',
                'LocationPanel',
                'OverlayInfoPanel',
                'OverlayDisplayPanel',
                'CanvasSettingsPanel',
                'AtlasPanel',
                'OverlayDisplayToolBar',
                'Scene3DToolBar',
                'FileTreePanel']


    @staticmethod
    def displayType():
        """Returns ``'3D'``, describing the type of display that the
        :class:`.Scene3DPanel` provides.
        """
        return '3D'


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``Scene3dPanel``.

        :arg parent:      A :mod:`wx` parent object.
        :arg overlayList: A :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        sceneOpts = scene3dopts.Scene3DOpts(self)

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         sceneOpts)


        # In 3D, the displaySpace must always be
        # set to world, regardless of the parent
        # DC value. This can be overridden manually
        # however (e.g. through the python shell)
        displayCtx.detachDisplaySpace()
        displayCtx.defaultDisplaySpace = 'world'
        displayCtx.displaySpace        = 'world'

        contentPanel = self.contentPanel

        self.__canvas = scene3dcanvas.WXGLScene3DCanvas(contentPanel,
                                                        overlayList,
                                                        displayCtx)

        opts = self.__canvas.opts

        opts.bindProps('pos',           displayCtx, 'location')
        opts.bindProps('showCursor',    sceneOpts)
        opts.bindProps('cursorColour',  sceneOpts)
        opts.bindProps('bgColour',      sceneOpts)
        opts.bindProps('showLegend',    sceneOpts)
        opts.bindProps('legendColour',  sceneOpts, 'fgColour')
        opts.bindProps('labelSize',     sceneOpts)
        opts.bindProps('light',         sceneOpts)
        opts.bindProps('lightPos',      sceneOpts)
        opts.bindProps('lightDistance', sceneOpts)
        opts.bindProps('showLight',     sceneOpts)
        opts.bindProps('zoom',          sceneOpts)
        opts.bindProps('offset',        sceneOpts)
        opts.bindProps('rotation',      sceneOpts)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.__canvas, flag=wx.EXPAND, proportion=1)
        contentPanel.SetSizer(sizer)

        self.centrePanelLayout()
        self.initProfile(scene3dviewprofile.Scene3DViewProfile)
        self.syncLocation = True


    def destroy(self):
        """Must be called when this ``Scene3DPanel`` is no longer in use.
        """

        self.__canvas.destroy()
        self.__canvas = None
        canvaspanel.CanvasPanel.destroy(self)


    def getGLCanvases(self):
        """Returns all of the :class:`.SliceCanvas` instances contained
        within this ``Scene3DPanel``.
        """
        return [self.__canvas]


    def getActions(self):
        """Overrides :meth:`.ViewPanel.getActions`. Returns a list of actions
        that can be executed on this ``Scene3DPanel``, and which will be added
        to its view menu.
        """
        actionz = [self.screenshot,
                   self.movieGif,
                   self.showCommandLineArgs,
                   self.applyCommandLineArgs,
                   None,
                   self.toggleDisplaySync,
                   self.resetDisplay]

        names = [a.actionName if a is not None else None for a in actionz]
        return list(zip(names, actionz))


    @actions.action
    def resetDisplay(self):
        """An action which resets the current camera configuration
        (zoom/pan/rotation). See the :meth:`.Scene3DViewProfile.resetDisplay`
        method.
        """
        self.currentProfile.resetDisplay()


    def getMovieFrame(self, overlay, opts):
        """Returns the current movie frame. If the :attr:`movieAxis` is ``3``
        (e.g. time series), the volume index is returned. Otherwise the
        current rotation matrix is returned.
        """
        if self.movieAxis == 3:
            return super(Scene3DPanel, self).getMovieFrame(overlay, opts)
        else:
            return np.copy(self.__canvas.opts.rotation)


    def doMovieUpdate(self, overlay, opts):
        """Overrides :meth:`.CanvasPanel.doMovieUpdate`. For x/y/z axis
        movies, the scene is rotated. Otherwise (for time) the ``CanvasPanel``
        implementation is called.
        """

        if self.movieAxis >= 3:
            return canvaspanel.CanvasPanel.doMovieUpdate(self, overlay, opts)
        else:

            canvas  = self.__canvas
            currot  = canvas.opts.rotation
            rate    = float(self.movieRate)
            rateMin = self.getAttribute('movieRate', 'minval')
            rateMax = self.getAttribute('movieRate', 'maxval')
            rate    = 0.1 + 0.9 * (rate - rateMin) / (rateMax - rateMin)
            rate    = rate * np.pi / 10

            rots                 = [0, 0, 0]
            rots[self.movieAxis] = rate

            xform = affine.axisAnglesToRotMat(*rots)
            xform = affine.concat(xform, currot)

            canvas.opts.rotation = xform
            return np.copy(xform)
