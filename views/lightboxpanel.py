#!/usr/bin/env python
#
# lightboxpanel.py - A panel which contains a LightBoxCanvas, for displaying
# multiple slices from a collection of overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`LightBoxPanel, a panel which contains a
:class:`.LightBoxCanvas`, for displaying multiple slices from a collection of
overlays.
"""

import logging
log = logging.getLogger(__name__)

import wx

import numpy as np

import fsl.utils.layout                           as fsllayout
import fsl.fsleyes.gl.wxgllightboxcanvas          as lightboxcanvas
import fsl.fsleyes.controls.lightboxtoolbar       as lightboxtoolbar
import fsl.fsleyes.controls.overlaydisplaytoolbar as overlaydisplaytoolbar
import fsl.fsleyes.displaycontext.lightboxopts    as lightboxopts
import canvaspanel


class LightBoxPanel(canvaspanel.CanvasPanel):
    """Convenience Panel which contains a :class:`.LightBoxCanvas` and a
    scrollbar, and sets up mouse-scrolling behaviour.
    """


    def __init__(self, parent, overlayList, displayCtx):
        """
        """

        sceneOpts = lightboxopts.LightBoxOpts()

        actionz = {
            'toggleLightBoxToolBar' : lambda *a: self.togglePanel(
                lightboxtoolbar.LightBoxToolBar, lb=self)
        }

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         sceneOpts,
                                         actionz)

        self._scrollbar = wx.ScrollBar(
            self.getCanvasPanel(),
            style=wx.SB_VERTICAL)
        
        self._lbCanvas  = lightboxcanvas.LightBoxCanvas(
            self.getCanvasPanel(),
            overlayList,
            displayCtx)

        self._lbCanvas.bindProps('zax',             sceneOpts)
        self._lbCanvas.bindProps('bgColour',        sceneOpts)
        self._lbCanvas.bindProps('cursorColour',    sceneOpts)
        self._lbCanvas.bindProps('showCursor',      sceneOpts)
        self._lbCanvas.bindProps('showGridLines',   sceneOpts)
        self._lbCanvas.bindProps('highlightSlice',  sceneOpts)
        self._lbCanvas.bindProps('renderMode',      sceneOpts)
        self._lbCanvas.bindProps('softwareMode',    sceneOpts)
        self._lbCanvas.bindProps('resolutionLimit', sceneOpts)

        # Bind these properties the other way around,
        # so that the sensible values calcualted by
        # the LBCanvas during its initialisation are
        # propagated to the LBOpts instance, rather
        # than the non-sensible default values in the
        # LBOpts instance.
        sceneOpts     .bindProps('nrows',           self._lbCanvas)
        sceneOpts     .bindProps('ncols',           self._lbCanvas)
        sceneOpts     .bindProps('topRow',          self._lbCanvas)
        sceneOpts     .bindProps('sliceSpacing',    self._lbCanvas)
        sceneOpts     .bindProps('zrange',          self._lbCanvas)

        self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.getCanvasPanel().SetSizer(self._canvasSizer)

        self._canvasSizer.Add(self._lbCanvas,  flag=wx.EXPAND, proportion=1)
        self._canvasSizer.Add(self._scrollbar, flag=wx.EXPAND)

        # When the display context location changes,
        # make sure the location is shown on the canvas
        self._lbCanvas.pos.xyz = self._displayCtx.location
        self._displayCtx .addListener('location',
                                      self._name,
                                      self._onLocationChange)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self._selectedOverlayChanged)

        sceneOpts.zoom = 750

        self._onLightBoxChange()
        self._onZoom()

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        sceneOpts.addListener(
            'ncols',        self._name, self._ncolsChanged)
        sceneOpts.addListener(
            'nrows',        self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'topRow',       self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'sliceSpacing', self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'zrange',       self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'zax',          self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'zoom',         self._name, self._onZoom)

        # When the scrollbar is moved,
        # update the canvas display
        self._scrollbar.Bind(wx.EVT_SCROLL, self._onScroll)

        self.Bind(wx.EVT_SIZE, self._onResize)

        self.Layout()

        self._selectedOverlayChanged()
        self.initProfile()

        # The FSLEyesFrame AuiManager seems to
        # struggle if we add these toolbars
        # immediately, so we'll do it asynchronously
        def addToolbars():
            
            self.togglePanel(overlaydisplaytoolbar.OverlayDisplayToolBar,
                             viewPanel=self)
            self.togglePanel(lightboxtoolbar.LightBoxToolBar, lb=self)

        wx.CallAfter(addToolbars)
            


    def destroy(self):
        """Removes property listeners"""

        self._displayCtx .removeListener('location',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        self._lbCanvas.destroy()

        canvaspanel.CanvasPanel.destroy(self)

        
    def _selectedOverlayChanged(self, *a):
        """Called when the selected overlay changes.

        Registers a listener on the :attr:`.Display.transform` property
        associated with the selected overlay, so that the
        :meth:`_transformChanged` method will be called on ``transform``
        changes.
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
                                 self._transformChanged)

        self._transformChanged()


    def _transformChanged(self, *a):
        """Called when the transform for the currently selected overlay
        changes.

        Updates the ``sliceSpacing`` and ``zrange`` properties to values
        sensible to the new overlay display space.
        """

        sceneOpts = self.getSceneOptions()
        overlay   = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        if overlay is None:
            return
        
        opts     = self._displayCtx.getOpts(overlay)
        loBounds = opts.bounds.getLo()
        hiBounds = opts.bounds.getHi()

        if opts.transform == 'id':
            sceneOpts.sliceSpacing = 1
            sceneOpts.zrange.x     = (0, overlay.shape[sceneOpts.zax] - 1)
        else:
            sceneOpts.sliceSpacing = overlay.pixdim[sceneOpts.zax]
            sceneOpts.zrange.x     = (loBounds[sceneOpts.zax],
                                      hiBounds[sceneOpts.zax])

        self._onResize()


    def getGLCanvases(self):
        """Returns a list of length 1, containing the :class:`.SliceCanvas`
        contained within this ``LightBoxPanel``.
        """
        return [self._lbCanvas]
        

    def getCanvas(self):
        """Returns a reference to the :class:`.LightBoxCanvas` instance (which
        is actually a :class:`.WXGLLightBoxCanvas`).
        """
        return self._lbCanvas

        
    def _onZoom(self, *a):
        """Called when the :attr:`zoom` property changes. Updates the
        number of columns on the lightbox canvas.
        """
        opts       = self.getSceneOptions()
        minval     = opts.getConstraint('zoom', 'minval')
        maxval     = opts.getConstraint('zoom', 'maxval')
        normZoom   = 1.0 - (opts.zoom - minval) / float(maxval)
        opts.ncols = int(1 + np.round(normZoom * 29))


    def _onResize(self, ev=None):
        """Called when the panel is resized. Automatically adjusts the
        number of lightbox rows to the maximum displayable number (given
        that the number of columns is fixed).
        """
        if ev is not None: ev.Skip()

        # Lay this panel out, so the
        # canvas panel size is up to date
        self.Layout()

        width,   height   = self._lbCanvas .GetClientSize().Get()
        sbWidth, sbHeight = self._scrollbar.GetClientSize().Get()

        width = width - sbWidth

        xlen = self._displayCtx.bounds.getLen(self._lbCanvas.xax)
        ylen = self._displayCtx.bounds.getLen(self._lbCanvas.yax)

        sliceWidth  = width / float(self._lbCanvas.ncols)
        sliceHeight = fsllayout.calcPixHeight(xlen, ylen, sliceWidth)

        if sliceHeight > 0: 
            self._lbCanvas.nrows = int(height / sliceHeight)


    def _onLocationChange(self, *a):
        """Called when the display context location changes.

        Updates the canvas location.
        """
        
        xpos = self._displayCtx.location.getPos(self._lbCanvas.xax)
        ypos = self._displayCtx.location.getPos(self._lbCanvas.yax)
        zpos = self._displayCtx.location.getPos(self._lbCanvas.zax)
        self._lbCanvas.pos.xyz = (xpos, ypos, zpos)


    def _ncolsChanged(self, *a):
        """Called when the lightbox canvas ``ncols`` property changes.
        Calculates the number of rows to display, and updates the
        scrollbar.
        """
        self._onResize()
        self._onLightBoxChange()


    def _onLightBoxChange(self, *a):
        """Called when any lightbox display properties change.

        Updates the scrollbar to reflect the change.
        """
        self._scrollbar.SetScrollbar(self._lbCanvas.topRow,
                                     self._lbCanvas.nrows,
                                     self._lbCanvas.getTotalRows(),
                                     self._lbCanvas.nrows,
                                     True)

        
    def _onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the top row displayed on the canvas.
        """
        self._lbCanvas.topRow = self._scrollbar.GetThumbPosition()
