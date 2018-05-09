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

import numpy as np

import fsleyes_widgets.utils.layout        as fsllayout

import fsleyes.actions                     as actions
import fsleyes.gl.wxgllightboxcanvas       as lightboxcanvas
import fsleyes.controls.lightboxtoolbar    as lightboxtoolbar
import fsleyes.displaycontext.lightboxopts as lightboxopts
from . import                                 canvaspanel


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


    The ``LightBoxPanel`` adds the following actions to those already
    provided by the :class:`.CanvasPanel`:

    .. autosummary::
       :nosignatures:

       toggleLightBoxToolBar
    """


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
        lbopts.bindProps('zax',             sceneOpts)
        lbopts.bindProps('bgColour',        sceneOpts)
        lbopts.bindProps('cursorColour',    sceneOpts)
        lbopts.bindProps('showCursor',      sceneOpts)
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
        sceneOpts.bindProps('nrows',        lbopts)
        sceneOpts.bindProps('ncols',        lbopts)
        sceneOpts.bindProps('topRow',       lbopts)
        sceneOpts.bindProps('sliceSpacing', lbopts)
        sceneOpts.bindProps('zrange',       lbopts)

        self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.contentPanel.SetSizer(self.__canvasSizer)

        self.__canvasSizer.Add(self.__lbCanvas, flag=wx.EXPAND, proportion=1)

        self.displayCtx .addListener('selectedOverlay',
                                     self.name,
                                     self.__selectedOverlayChanged)
        self.displayCtx .addListener('displaySpace',
                                     self.name,
                                     self.__radioOrientationChanged)
        self.displayCtx .addListener('radioOrientation',
                                     self.name,
                                     self.__radioOrientationChanged)
        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__selectedOverlayChanged)

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        sceneOpts.addListener(
            'ncols',        self.name, self.__ncolsChanged)
        sceneOpts.addListener(
            'nrows',        self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'topRow',       self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'sliceSpacing', self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zrange',       self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zax',          self.name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zoom',         self.name, self.__onZoom)

        # When the scrollbar is moved,
        # update the canvas display
        self.__scrollbar.Bind(wx.EVT_SCROLL, self.__onScroll)

        self.Bind(wx.EVT_SIZE, self.__onResize)

        sceneOpts.zoom = 750

        self.__onLightBoxChange()
        self.__onZoom()

        self.__selectedOverlayChanged()
        self.centrePanelLayout()
        self.initProfile()


    def destroy(self):
        """Must be called when this ``LightBoxPanel`` is closed.

        Removes property listeners, destroys the :class:`.LightBoxCanvas`,
        and calls :meth:`.CanvasPanel.destroy`.
        """

        self.displayCtx .removeListener('selectedOverlay',  self.name)
        self.displayCtx .removeListener('displaySpace',     self.name)
        self.displayCtx .removeListener('radioOrientation', self.name)
        self.overlayList.removeListener('overlays',         self.name)

        canvaspanel.CanvasPanel.destroy(self)

        self.__lbCanvas.destroy()
        self.__lbCanvas = None


    @actions.toggleControlAction(lightboxtoolbar.LightBoxToolBar)
    def toggleLightBoxToolBar(self):
        """Shows/hides a :class:`.LightBoxToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(lightboxtoolbar.LightBoxToolBar, lb=self)


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``LightBoxPanel``.
        """
        actions = [self.screenshot,
                   self.showCommandLineArgs,
                   self.applyCommandLineArgs,
                   None,
                   self.toggleMovieMode,
                   self.toggleDisplaySync,
                   None,
                   self.toggleOverlayList,
                   self.toggleLocationPanel,
                   self.toggleOverlayInfo,
                   self.toggleDisplayPanel,
                   self.toggleCanvasSettingsPanel,
                   self.toggleAtlasPanel,
                   self.toggleDisplayToolBar,
                   self.toggleLightBoxToolBar,
                   self.toggleLookupTablePanel,
                   self.toggleClusterPanel,
                   self.toggleClassificationPanel,
                   self.removeAllPanels]

        names = [a.__name__ if a is not None else None for a in actions]

        return list(zip(names, actions))


    def getGLCanvases(self):
        """Returns a list containing the :class:`.LightBoxCanvas` contained
        within this ``LightBoxPanel``.
        """
        return [self.__lbCanvas]


    def getCanvas(self):
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


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.

        If the currently selected overlay is a :class:`.Nifti` instance, or
        has an associated reference image (see
        :meth:`.DisplayOpts.referenceImage`), a listener is registered on
        the reference image :attr:`.NiftiOpts.transform` property, so that the
        :meth:`__transformChanged` method will be called when it changes.
        """

        if len(self.overlayList) == 0:
            return

        selectedOverlay = self.displayCtx.getSelectedOverlay()

        for overlay in self.overlayList:

            refImage = self.displayCtx.getReferenceImage(overlay)

            if refImage is None:
                continue

            opts = self.displayCtx.getOpts(refImage)

            opts.removeListener('transform', self.name)

            if overlay == selectedOverlay:
                opts.addListener('transform',
                                 self.name,
                                 self.__transformChanged)

        # If the current zrange is [0, 0]
        # we'll assume that the spacing/
        # zrange need to be initialised.
        lbCanvas = self.__lbCanvas
        opts     = self.sceneOpts

        if opts.zrange == [0.0, 0.0]:

            opts.sliceSpacing = lbCanvas.calcSliceSpacing(selectedOverlay)
            opts.zrange       = self.displayCtx.bounds.getRange(opts.zax)


    def __transformChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.transform` property for the
        reference image of the currently selected overlay changes.

        Updates the :attr:`.LightBoxOpts.sliceSpacing` and
        :attr:`.LightBoxOpts.zrange` properties to values sensible to the
        new overlay display space.
        """

        sceneOpts = self.sceneOpts
        overlay   = self.displayCtx.getReferenceImage(
            self.displayCtx.getSelectedOverlay())

        if overlay is None:
            return

        opts     = self.displayCtx.getOpts(overlay)
        loBounds = opts.bounds.getLo()
        hiBounds = opts.bounds.getHi()

        # Reset the spacing/zrange. Not
        # sure if this is the best idea,
        # but it's here for the time being.
        sceneOpts.sliceSpacing = self.__lbCanvas.calcSliceSpacing(overlay)
        sceneOpts.zrange.x     = (loBounds[sceneOpts.zax],
                                  hiBounds[sceneOpts.zax])

        self.__onResize()


    def __onZoom(self, *a):
        """Called when the :attr:`.SceneOpts.zoom` property changes. Updates
        the number of slice columns shown.
        """
        opts       = self.sceneOpts
        minval     = opts.getAttribute('zoom', 'minval')
        maxval     = opts.getAttribute('zoom', 'maxval')
        normZoom   = 1.0 - (opts.zoom - minval) / float(maxval)
        opts.ncols = int(1 + np.round(normZoom * 29))


    def __onResize(self, ev=None):
        """Called when the panel is resized. Automatically adjusts the number
        of rows to the maximum displayable number (given that the number of
        columns is fixed).
        """
        if ev is not None: ev.Skip()

        # Lay this panel out, so the
        # canvas panel size is up to date
        self.Layout()

        lbcanvas          = self.__lbCanvas
        lbopts            = lbcanvas.opts
        width,   height   = lbcanvas        .GetClientSize().Get()
        sbWidth, sbHeight = self.__scrollbar.GetClientSize().Get()

        width = width - sbWidth

        xlen = self.displayCtx.bounds.getLen(lbopts.xax)
        ylen = self.displayCtx.bounds.getLen(lbopts.yax)

        sliceWidth  = width / float(lbopts.ncols)
        sliceHeight = fsllayout.calcPixHeight(xlen, ylen, sliceWidth)

        if sliceHeight > 0:
            lbopts.nrows = int(height / sliceHeight)


    def __ncolsChanged(self, *a):
        """Called when the :attr:`.LightBoxOpts.ncols` property changes.
        Calculates the number of rows to display, and updates the
        scrollbar.
        """
        self.__onResize()
        self.__onLightBoxChange()


    def __onLightBoxChange(self, *a):
        """Called when any :class:`.LightBoxOpts` property changes.

        Updates the scrollbar to reflect the change.
        """
        canvas = self.__lbCanvas
        opts   = canvas.opts
        self.__scrollbar.SetScrollbar(opts.topRow,
                                      opts.nrows,
                                      canvas.getTotalRows(),
                                      opts.nrows,
                                      True)


    def __onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the top row displayed on the :class:`.LightBoxCanvas`.
        """
        self.__lbCanvas.opts.topRow = self.__scrollbar.GetThumbPosition()
