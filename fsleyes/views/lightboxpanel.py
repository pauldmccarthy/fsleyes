#!/usr/bin/env python
#
# lightboxpanel.py - A panel which contains a LightBoxCanvas, for displaying
# multiple slices from a collection of overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxPanel`, which displays multiple
2D slices of 3D overlays.
"""

import logging

import wx

import fsleyes_props                        as props

import fsleyes.gl.wxgllightboxcanvas        as lightboxcanvas
import fsleyes.profiles.lightboxviewprofile as lightboxviewprofile
import fsleyes.displaycontext.lightboxopts  as lightboxopts
import fsleyes.views.canvaspanel            as canvaspanel


log = logging.getLogger(__name__)


class LightBoxPanel(canvaspanel.CanvasPanel):
    """The ``LightBoxPanel`` is a *FSLeyes view* which is capable of
    displaying multiple 2D slices of the 3D overlays conatined in an
    :class:`.OverlayList`. A ``LightBoxPanel`` looks something like the
    following:

    .. image:: images/lightboxpanel.png
       :scale: 50%
       :align: center


    The ``LightBoxPanel`` uses a :class:`.LightBoxCanvas` panel to display
    the slices, and a :class:`.LightBoxOpts` instance to manage the display
    settings. The canvas is accessed through the :meth:`getCanvas` and
    :meth:`getGLCanvases` methods, and the ``LightBoxOpts`` instanace can
    be retrieved via the :meth:`.CanvasPanel.sceneOpts` property.
    """


    @staticmethod
    def defaultLayout():
        """Returns a list of control panel types to be added for the default
        lightbox panel layout.
        """
        return ['OverlayDisplayToolBar',
                'LightBoxToolBar',
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
                'LigbhtBoxToolBar',
                'FileTreePanel']


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``LightBoxPanel``.

        :arg parent:      A :mod:`wx` parent object.
        :arg overlayList: A :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        sceneOpts = lightboxopts.LightBoxOpts(self)

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         sceneOpts)

        self.__scrollbar = wx.ScrollBar(self.centrePanel, style=wx.SB_VERTICAL)
        self.__lbCanvas  = lightboxcanvas.WXGLLightBoxCanvas(
            self.contentPanel,
            overlayList,
            displayCtx)

        lbopts = self.__lbCanvas.opts

        lbopts.bindProps('pos', displayCtx, 'location')
        lbopts.bindProps('bgColour',        sceneOpts)
        lbopts.bindProps('cursorColour',    sceneOpts)
        lbopts.bindProps('showCursor',      sceneOpts)
        lbopts.bindProps('cursorWidth',     sceneOpts)
        lbopts.bindProps('showGridLines',   sceneOpts)
        lbopts.bindProps('highlightSlice',  sceneOpts)
        lbopts.bindProps('renderMode',      sceneOpts)
        lbopts.bindProps('highDpi',         sceneOpts)

        # Bind these properties the other way around,
        # so that the sensible values calcualted by
        # the LBCanvas during its initialisation are
        # propagated to the LBOpts instance, rather
        # than the non-sensible default values in the
        # LBOpts instance.
        sceneOpts.bindProps('zax',          lbopts)
        sceneOpts.bindProps('sliceSpacing', lbopts)
        sceneOpts.bindProps('zrange',       lbopts)
        sceneOpts.bindProps('lockZrange',   lbopts)
        sceneOpts.bindProps('zoom',         lbopts)

        self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.contentPanel.SetSizer(self.__canvasSizer)

        self.__canvasSizer.Add(self.__lbCanvas, flag=wx.EXPAND, proportion=1)

        self.displayCtx .addListener('displaySpace',
                                     self.name,
                                     self.__radioOrientationChanged)
        self.displayCtx .addListener('radioOrientation',
                                     self.name,
                                     self.__radioOrientationChanged)
        self.overlayList .addListener('overlays',
                                     self.name,
                                     self.__radioOrientationChanged)

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        sceneOpts.addListener(
            'sliceSpacing', self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zrange',       self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zax',          self.name, self.__onLightBoxChange)

        # When the scrollbar is moved,
        # update the canvas display
        self.__scrollbar.Bind(wx.EVT_SCROLL, self.__onScroll)

        self.__onLightBoxChange()

        self.centrePanelLayout()
        self.initProfile(lightboxviewprofile.LightBoxViewProfile)


    def destroy(self):
        """Must be called when this ``LightBoxPanel`` is closed.

        Removes property listeners, destroys the :class:`.LightBoxCanvas`,
        and calls :meth:`.CanvasPanel.destroy`.
        """

        self.displayCtx .removeListener('displaySpace',     self.name)
        self.displayCtx .removeListener('radioOrientation', self.name)

        canvaspanel.CanvasPanel.destroy(self)

        self.__lbCanvas.destroy()
        self.__lbCanvas = None


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``LightBoxPanel``.
        """
        actionz = [self.screenshot,
                   self.showCommandLineArgs,
                   self.applyCommandLineArgs,
                   None,
                   self.toggleMovieMode,
                   self.toggleDisplaySync]

        names = [a.actionName if a is not None else None for a in actionz]
        return list(zip(names, actionz))


    def getGLCanvases(self):
        """Returns a list containing the :class:`.LightBoxCanvas` contained
        within this ``LightBoxPanel``.
        """
        return [self.__lbCanvas]


    def getCanvas(self):
        """Returns a reference to the :class:`.LightBoxCanvas` instance. """
        return self.__lbCanvas


    @property
    def canvas(self):
        """Returns a reference to the :class:`.LightBoxCanvas` instance. """
        return self.__lbCanvas


    def centrePanelLayout(self):
        """Overrides :meth:`.CanvasPanel.centrePanelLayout`. Adds the
        scrollbar to the centre panel.
        """

        self.layoutContainerPanel()

        centrePanel    = self.centrePanel
        containerPanel = self.containerPanel
        sizer          = wx.BoxSizer(wx.HORIZONTAL)

        centrePanel.SetSizer(sizer)

        sizer.Add(containerPanel,   flag=wx.EXPAND, proportion=1)
        sizer.Add(self.__scrollbar, flag=wx.EXPAND)

        self.PostSizeEvent()


    def __radioOrientationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` or
        :attr:`.DisplayContext.radioOrientation` properties change. Updates the
        :attr:`.LightBoxCanvas.invertX` property as needed.
        """

        lbopts  = self.__lbCanvas.opts
        inRadio = self.displayCtx.displaySpaceIsRadiological()
        flip    = self.displayCtx.radioOrientation != inRadio
        flip    = flip and lbopts.zax in (1, 2)

        lbopts.invertX = flip


    def __onLightBoxChange(self, *a):
        """Called when any :class:`.LightBoxOpts` property changes.

        Updates the scrollbar to reflect the current number of slices being
        displayed.
        """
        canvas  = self.canvas
        copts   = canvas.opts
        start   = copts.startslice
        end     = copts.maxslices
        nslices = canvas.nslices
        if canvas.nslices == 0:
            start   = 0
            end     = 1
            nslices = 1
        self.__scrollbar.SetScrollbar(start, nslices, end, nslices, True)


    def __onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the Z range displayed on the :class:`.LightBoxCanvas`.
        """
        self.scrollpos = self.__scrollbar.GetThumbPosition()


    @property
    def scrollpos(self):
        """Returns the current scroll position - the index of the first
        displayed slice on the canvas.
        """
        return self.__scrollbar.GetThumbPosition()


    @scrollpos.setter
    def scrollpos(self, sliceno):
        """Set the current scroll position - the index of the first
        displayed slice on the canvas. Called when the scroll bar is
        moved, and from the :class:`.LightBoxViewProfile`.
        """

        canvas = self.canvas
        opts   = self.sceneOpts
        copts  = canvas.opts
        zlen   = copts.zrange.xlen

        if sliceno < 0 or sliceno >= copts.maxslices:
            return

        self.__scrollbar.SetThumbPosition(sliceno)

        # Expand the z range if the it does not
        # take up the full grid size (i.e. the
        # last row contains fewer slices than
        # can be displayed),
        nslices  = copts.nslices
        gridsize = canvas.nrows * canvas.ncols
        zpos     = copts.slices[sliceno]

        if nslices < gridsize:
            diff = gridsize - nslices
            zlen = zlen + diff * copts.sliceSpacing

        with props.skip(opts, 'zrange', self.name):
            copts.zrange = zpos, zpos + zlen
