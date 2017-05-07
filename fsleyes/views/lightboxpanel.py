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
    be retrieved via the :meth:`.CanvasPanel.getSceneOptions` method.


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

        sceneOpts = lightboxopts.LightBoxOpts()

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         sceneOpts)

        self.__scrollbar = wx.ScrollBar(
            self.getCentrePanel(),
            style=wx.SB_VERTICAL)

        self.__lbCanvas  = lightboxcanvas.WXGLLightBoxCanvas(
            self.getContentPanel(),
            overlayList,
            displayCtx)

        self.__lbCanvas.bindProps('zax',             sceneOpts)
        self.__lbCanvas.bindProps('bgColour',        sceneOpts)
        self.__lbCanvas.bindProps('cursorColour',    sceneOpts)
        self.__lbCanvas.bindProps('showCursor',      sceneOpts)
        self.__lbCanvas.bindProps('showGridLines',   sceneOpts)
        self.__lbCanvas.bindProps('highlightSlice',  sceneOpts)
        self.__lbCanvas.bindProps('renderMode',      sceneOpts)

        # Bind these properties the other way around,
        # so that the sensible values calcualted by
        # the LBCanvas during its initialisation are
        # propagated to the LBOpts instance, rather
        # than the non-sensible default values in the
        # LBOpts instance.
        sceneOpts.bindProps('nrows',        self.__lbCanvas)
        sceneOpts.bindProps('ncols',        self.__lbCanvas)
        sceneOpts.bindProps('topRow',       self.__lbCanvas)
        sceneOpts.bindProps('sliceSpacing', self.__lbCanvas)
        sceneOpts.bindProps('zrange',       self.__lbCanvas)

        self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.getContentPanel().SetSizer(self.__canvasSizer)

        self.__canvasSizer.Add(self.__lbCanvas, flag=wx.EXPAND, proportion=1)

        # When the display context location changes,
        # make sure the location is shown on the canvas
        self.__lbCanvas.pos.xyz = self._displayCtx.location
        self._displayCtx .addListener('location',
                                      self._name,
                                      self.__onLocationChange)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)
        self._displayCtx .addListener('displaySpace',
                                      self._name,
                                      self.__radioOrientationChanged)
        self._displayCtx .addListener('radioOrientation',
                                      self._name,
                                      self.__radioOrientationChanged)
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__selectedOverlayChanged)

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        sceneOpts.addListener(
            'ncols',        self._name, self.__ncolsChanged)
        sceneOpts.addListener(
            'nrows',        self._name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'topRow',       self._name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'sliceSpacing', self._name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zrange',       self._name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zax',          self._name, self.__onLightBoxChange)
        sceneOpts.addListener(
            'zoom',         self._name, self.__onZoom)

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

        self._displayCtx .removeListener('location',         self._name)
        self._displayCtx .removeListener('selectedOverlay',  self._name)
        self._displayCtx .removeListener('displaySpace',     self._name)
        self._displayCtx .removeListener('radioOrientation', self._name)
        self._overlayList.removeListener('overlays',         self._name)

        self.__lbCanvas.destroy()

        canvaspanel.CanvasPanel.destroy(self)


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

        centrePanel    = self.getCentrePanel()
        containerPanel = self.getContainerPanel()
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

        inRadio = self._displayCtx.displaySpaceIsRadiological()
        flip    = self._displayCtx.radioOrientation != inRadio
        flip    = flip and self.__lbCanvas.zax in (1, 2)

        self.__lbCanvas.invertX = flip


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.

        If the currently selected overlay is a :class:`.Nifti` instance, or
        has an associated reference image (see
        :meth:`.DisplayOpts.getReferenceImage`), a listener is registered on
        the reference image :attr:`.NiftiOpts.transform` property, so that the
        :meth:`__transformChanged` method will be called when it changes.
        """

        if len(self._overlayList) == 0:
            return

        selectedOverlay = self._displayCtx.getSelectedOverlay()

        for overlay in self._overlayList:

            refImage = self._displayCtx.getReferenceImage(overlay)

            if refImage is None:
                continue

            opts = self._displayCtx.getOpts(refImage)

            opts.removeListener('transform', self._name)

            if overlay == selectedOverlay:
                opts.addListener('transform',
                                 self._name,
                                 self.__transformChanged)

        # If the current zrange is [0, 0]
        # we'll assume that the spacing/
        # zrange need to be initialised.
        lbCanvas = self.__lbCanvas
        opts     = self.getSceneOptions()

        if opts.zrange == [0.0, 0.0]:

            opts.sliceSpacing = lbCanvas.calcSliceSpacing(selectedOverlay)
            opts.zrange       = self._displayCtx.bounds.getRange(opts.zax)


    def __transformChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.transform` property for the
        reference image of the currently selected overlay changes.

        Updates the :attr:`.LightBoxOpts.sliceSpacing` and
        :attr:`.LightBoxOpts.zrange` properties to values sensible to the
        new overlay display space.
        """

        sceneOpts = self.getSceneOptions()
        overlay   = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        if overlay is None:
            return

        opts     = self._displayCtx.getOpts(overlay)
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
        opts       = self.getSceneOptions()
        minval     = opts.getConstraint('zoom', 'minval')
        maxval     = opts.getConstraint('zoom', 'maxval')
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

        width,   height   = self.__lbCanvas .GetClientSize().Get()
        sbWidth, sbHeight = self.__scrollbar.GetClientSize().Get()

        width = width - sbWidth

        xlen = self._displayCtx.bounds.getLen(self.__lbCanvas.xax)
        ylen = self._displayCtx.bounds.getLen(self.__lbCanvas.yax)

        sliceWidth  = width / float(self.__lbCanvas.ncols)
        sliceHeight = fsllayout.calcPixHeight(xlen, ylen, sliceWidth)

        if sliceHeight > 0:
            self.__lbCanvas.nrows = int(height / sliceHeight)


    def __onLocationChange(self, *a):
        """Called when the :attr:`.DisplayContext.location` changes.

        Updates the location shown on the :class:`.LightBoxCanvas`.
        """

        xpos = self._displayCtx.location.getPos(self.__lbCanvas.xax)
        ypos = self._displayCtx.location.getPos(self.__lbCanvas.yax)
        zpos = self._displayCtx.location.getPos(self.__lbCanvas.zax)
        self.__lbCanvas.pos.xyz = (xpos, ypos, zpos)


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
        self.__scrollbar.SetScrollbar(self.__lbCanvas.topRow,
                                      self.__lbCanvas.nrows,
                                      self.__lbCanvas.getTotalRows(),
                                      self.__lbCanvas.nrows,
                                      True)


    def __onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the top row displayed on the :class:`.LightBoxCanvas`.
        """
        self.__lbCanvas.topRow = self.__scrollbar.GetThumbPosition()
