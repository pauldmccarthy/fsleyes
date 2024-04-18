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

import          wx
import numpy as np

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

    The ``LightBoxPanel`` adds scrolling capability to the ``LightBoxCanvas``
    - a scroll bar is displayed which can be used to scroll through the
    slices.  This is achieved by adjusting the
    :attr:`.LightBoxCanvasOpts.zrange` property.
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


    @staticmethod
    def toolOrder():
        """Returns a list of tool names, specifying the order in which they
        should appear in the FSLeyes lightbox panel settings menu.
        """
        return ['LightBoxSampleAction']


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

        name   = self.name
        lbopts = self.__lbCanvas.opts

        lbopts.bind('pos', displayCtx, 'location')
        lbopts.bind('bgColour',        sceneOpts)
        lbopts.bind('cursorColour',    sceneOpts)
        lbopts.bind('showCursor',      sceneOpts)
        lbopts.bind('cursorWidth',     sceneOpts)
        lbopts.bind('showGridLines',   sceneOpts)
        lbopts.bind('highlightSlice',  sceneOpts)
        lbopts.bind('labelSpace',      sceneOpts)
        lbopts.bind('labelSize',       sceneOpts)
        lbopts.bind('fgColour',        sceneOpts)
        lbopts.bind('renderMode',      sceneOpts)

        # Bind these properties the other way around,
        # so that the sensible values calcualted by
        # the LBCanvas during its initialisation are
        # propagated to the LBOpts instance, rather
        # than the non-sensible default values in the
        # LBOpts instance.
        sceneOpts.bind('zax',            lbopts)
        sceneOpts.bind('sliceSpacing',   lbopts)
        sceneOpts.bind('sliceOverlap',   lbopts)
        sceneOpts.bind('sampleSlices',   lbopts)
        sceneOpts.bind('reverseOverlap', lbopts)
        sceneOpts.bind('reverseSlices',  lbopts)
        sceneOpts.bind('zrange',         lbopts)
        sceneOpts.bind('nrows',          lbopts)
        sceneOpts.bind('ncols',          lbopts)
        sceneOpts.bind('zoom',           lbopts)

        self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.contentPanel.SetSizer(self.__canvasSizer)

        self.__canvasSizer.Add(self.__lbCanvas, flag=wx.EXPAND, proportion=1)

        displayCtx .listen('displaySpace', name,
                           self.__radioOrientationChanged)
        displayCtx .listen('radioOrientation', name,
                           self.__radioOrientationChanged)
        overlayList.listen('overlays', name,
                           self.__radioOrientationChanged)

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        sceneOpts.listen( 'sliceSpacing', name, self.__onLightBoxChange)
        sceneOpts.listen( 'zrange',       name, self.__onLightBoxChange)
        sceneOpts.listen( 'zax',          name, self.__onLightBoxChange)
        sceneOpts.listen( 'nrows',        name, self.__onLightBoxChange)
        sceneOpts.listen( 'ncols',        name, self.__onLightBoxChange)
        self.Bind(wx.EVT_SIZE,                  self.__onLightBoxChange)
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

        self.displayCtx .remove('displaySpace',     self.name)
        self.displayCtx .remove('radioOrientation', self.name)
        self.overlayList.removeListener('overlays', self.name)

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
        nrows   = canvas.nrows
        nslices = canvas.nslices

        if nrows == 0 or nslices >= copts.maxslices:
            start   = 0
            end     = 1
            nslices = 1
        else:
            start = canvas.toprow
            end   = canvas.maxrows

        self.__scrollbar.SetScrollbar(start, nrows, end, nrows, True)


    def __onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the Z range displayed on the :class:`.LightBoxCanvas`.
        """
        self.scrollpos = self.__scrollbar.GetThumbPosition()


    @property
    def scrollpos(self):
        """Returns the current scroll position - the index of the first
        displayed row on the canvas.
        """
        return self.__scrollbar.GetThumbPosition()


    @scrollpos.setter
    def scrollpos(self, row):
        """Set the current scroll position - the index of the first
        displayed row on the canvas. Called when the scroll bar is
        moved, and from the :class:`.LightBoxViewProfile`.
        """

        canvas  = self.canvas
        opts    = self.sceneOpts
        copts   = canvas.opts
        zlen    = copts.normzlen
        row     = np.clip(row, 0, canvas.maxrows)
        sliceno = np.clip(row * canvas.ncols, 0, copts.maxslices - 1)

        self.__scrollbar.SetThumbPosition(row)
        self.__scrollbar.Refresh()

        # Expand the z range if it does not
        # take up the full grid size (i.e.
        # the last row contains fewer
        # slices than can be displayed),
        nslices  = copts.nslices
        gridsize = canvas.nslices
        if nslices < gridsize:
            diff = gridsize - nslices
            zlen = zlen + diff * copts.sliceSpacing

        # Calculate the z position corresponding
        # to the new row, then calculate the new
        # z range from this slice position.
        zpos           = copts.slices[sliceno]
        newzlo, newzhi = zpos, zpos + zlen

        # Limit the zrange to [0, 1], keeping
        # the z length constant
        if newzlo < 0:
            newzhi -= newzlo
            newzlo  = 0
        elif newzhi > 1:
            newzlo -= (newzhi - 1)
            newzhi  = 1

        with props.skip(opts, 'zrange', self.name):
            copts.zrange = newzlo, newzhi
