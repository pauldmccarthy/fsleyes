#!/usr/bin/env python
#
# histogrampanel.py - The HistogramPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramPanel`, which is a *FSLeyes view*
that plots the histogram of data from :class:`.Image` overlays.
"""


import logging

import wx

import numpy as np

import fsl.data.image                         as fslimage
import fsleyes_props                          as props

import fsleyes.actions                        as actions
import fsleyes.overlay                        as fsloverlay
import fsleyes.plotting.histogramseries       as histogramseries
import fsleyes.controls.histogramcontrolpanel as histogramcontrolpanel
import fsleyes.controls.histogramtoolbar      as histogramtoolbar
from . import                                    plotpanel


log = logging.getLogger(__name__)


class HistogramPanel(plotpanel.OverlayPlotPanel):
    """An :class:`.OverlayPlotPanel` which plots histograms from
    :class:`.Image`     overlay data. A ``HistogramPanel`` looks something
    like this:

    .. image:: images/histogrampanel.png
       :scale: 50%
       :align: center


    A ``HistogramPanel`` plots one or more :class:`HistogramSeries` instances,
    each of which encapsulate histogram data from an :class:`.Image` overlay.


    A couple of control panels may be shown on a ``HistogramPanel``:

    .. autosummary::
       :nosignatures:

       ~fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsleyes.controls.histogramcontrolpanel.HistogramControlPanel


    The following :mod:`actions` are provided, in addition to those already
    provided by the :class:`.PlotPanel`:

    .. autosummary::
       :nosignatures:

       toggleHistogramToolBar
       toggleHistogramControl
    """


    histType = props.Choice(('probability', 'count'))
    """The histogram type:

    =============== ==========================================================
    ``count``       The y axis represents the absolute number of values within
                    each bin
    ``probability`` The y axis represents the number of values within each
                    bin, divided by the total number of values.
    =============== ==========================================================
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``HistogramPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        plotpanel.OverlayPlotPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__currentHs = None

        self       .addListener('histType', self._name, self.draw)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.initProfile()
        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes some property listeners, and calls
        :meth:`.PlotPanel.destroy`.
        """

        self.__currentHs = None

        self             .removeListener('histType',        self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        plotpanel.OverlayPlotPanel.destroy(self)


    @actions.toggleControlAction(histogramcontrolpanel.HistogramControlPanel)
    def toggleHistogramControl(self, floatPane=False):
        """Shows/hides a :class:`.HistogramControlPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(histogramcontrolpanel.HistogramControlPanel,
                         self,
                         location=wx.RIGHT,
                         floatPane=floatPane)


    @actions.toggleControlAction(histogramtoolbar.HistogramToolBar)
    def toggleHistogramToolBar(self):
        """Shows/hides a :class:`.HistogramToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(histogramtoolbar.HistogramToolBar, histPanel=self)


    @actions.toggleAction
    def toggleHistogramOverlay(self):
        """Toggles the value of the :attr:`.HistogramSeries.showOverlay`
        for the currently selected overlay (if possible).
        """
        # This action gets configured in the
        # __selectedOverlayChanged method
        pass


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``HistogramPanel``.
        """
        actions = [self.screenshot,
                   self.importDataSeries,
                   self.exportDataSeries,
                   None,
                   self.toggleOverlayList,
                   self.togglePlotList,
                   self.toggleHistogramToolBar,
                   self.toggleHistogramControl,
                   self.toggleHistogramOverlay]

        names = [a.__name__ if a is not None else None for a in actions]

        return list(zip(names, actions))


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Passes some
        :class:`.HistogramSeries` instances to the
        :meth:`.PlotPanel.drawDataSeries` method.
        """

        if not self or self.destroyed():
            return

        hss = self.getDataSeriesToPlot()

        for hs in hss:
            with props.suppress(hs, 'label'):
                hs.label = self._displayCtx.getDisplay(hs.overlay).name

        if self.smooth:
            self.drawDataSeries(hss)
        else:
            self.drawDataSeries(hss, drawstyle='steps-pre')

        self.drawArtists()


    def createDataSeries(self, overlay):
        """Creates a :class:`.HistogramSeries` instance for the specified
        overlay.
        """

        if not isinstance(overlay, fslimage.Image):
            return None, None, None

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        hs = histogramseries.HistogramSeries(overlay,
                                             self._displayCtx,
                                             self._overlayList)

        hs.colour      = self.getOverlayPlotColour(overlay)
        hs.alpha       = 1
        hs.lineWidth   = 1
        hs.lineStyle   = '-'

        return hs, [], []


    def prepareDataSeries(self, hs):
        """Overrides :meth:`.PlotPanel.prepareDataSeries`.

        Performs some pre-processing on the data contained in the given
        :class:`.HistogramSeries` instance.
        """

        xdata, ydata = hs.getData()

        if len(xdata) == 0 or len(ydata) == 0:
            return [], []

        # If smoothing is not enabled, we'll
        # munge the histogram data a bit so
        # that plt.plot(drawstyle='steps-pre')
        # plots it nicely.
        if not self.smooth:
            xpad = np.zeros(len(xdata) + 1, dtype=np.float32)
            ypad = np.zeros(len(ydata) + 2, dtype=np.float32)

            xpad[ :-1] = xdata
            xpad[  -1] = xdata[-1]
            ypad[1:-1] = ydata
            xdata      = xpad
            ydata      = ypad

        # If smoothing is enabled, the above munge
        # is not necessary, and will probably cause
        # the spline interpolation (performed by
        # the PlotPanel) to fail.
        else:
            xdata = np.array(xdata[:-1], dtype=np.float32)
            ydata = np.array(ydata,      dtype=np.float32)

        # The passed-in series may just
        # be a DataSeries instance.
        if not isinstance(hs, histogramseries.HistogramSeries):
            return xdata, ydata

        # Or a HistogramSeries instance
        nvals = hs.getNumHistogramValues()
        if   self.histType == 'count':       return xdata, ydata
        elif self.histType == 'probability': return xdata, ydata / nvals


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.selectedOverlay` changes. Configures the
        :meth:`toggleHistogramOverlay` action.
        """

        overlay = self._displayCtx.getSelectedOverlay()
        oldHs   = self.__currentHs
        newHs   = self.getDataSeries(overlay)
        enable  = (overlay is not None) and \
                  (newHs   is not None) and \
                  isinstance(overlay, fslimage.Image)

        self.toggleHistogramOverlay.enabled = enable

        if not enable or (oldHs is newHs):
            return

        self.__currentHs = newHs

        if oldHs is not None:
            self.toggleHistogramOverlay.unbindProps(
                'toggled', oldHs, 'showOverlay')

        self.toggleHistogramOverlay.bindProps(
            'toggled', newHs, 'showOverlay')
