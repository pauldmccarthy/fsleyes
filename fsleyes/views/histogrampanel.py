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

import numpy as np

import fsl.data.image                    as fslimage
import fsl.data.mesh                     as fslmesh
import fsleyes_props                     as props

import fsleyes.actions                   as actions
import fsleyes.overlay                   as fsloverlay
import fsleyes.views.plotpanel           as plotpanel
import fsleyes.profiles.histogramprofile as histogramprofile
import fsleyes.plotting.histogramseries  as histogramseries



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


    A couple of control panels may be shown on a ``HistogramPanel``, via
    :meth:`.ViewPanel.togglePanel`:

    .. autosummary::
       :nosignatures:

       ~fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsleyes.controls.histogramcontrolpanel.HistogramControlPanel
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


    plotType = props.Choice(('centre', 'edge'))
    """How histograms are plotted:

    ========== ==========================================================
    ``centre`` Plot one data point at the centre of each bin
    ``edge``   Plot one data point at each bin edge - this produces a
               "stepped" plot.
    ========== ==========================================================
    """


    @staticmethod
    def defaultLayout():
        """Returns a list of control panel types to be added for the default
        histogram panel layout.
        """
        return ['HistogramToolBar',
                'OverlayListPanel',
                'PlotListPanel']


    @staticmethod
    def controlOrder():
        """Returns a list of control panel names, specifying the order in
        which they should appear in the  FSLeyes ortho panel settings menu.
        """
        return ['OverlayListPanel',
                'PlotListPanel',
                'HistogramToolBar',
                'HistogramControlPanel']


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

        self       .addListener('histType', self.name, self.draw)
        self       .addListener('plotType', self.name, self.draw)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)

        self.initProfile(histogramprofile.HistogramProfile)
        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes some property listeners, and calls
        :meth:`.PlotPanel.destroy`.
        """

        self.__currentHs = None

        self            .removeListener('histType',        self.name)
        self            .removeListener('plotType',        self.name)
        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        plotpanel.OverlayPlotPanel.destroy(self)


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
        actionz = [self.screenshot,
                   self.importDataSeries,
                   self.exportDataSeries,
                   self.toggleHistogramOverlay]

        names = [a.actionName if a is not None else None for a in actionz]
        return list(zip(names, actionz))


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Passes some
        :class:`.HistogramSeries` instances to the
        :meth:`.PlotPanel.drawDataSeries` method.
        """

        if not self or self.destroyed:
            return

        canvas = self.canvas
        hss    = self.getDataSeriesToPlot()

        for hs in hss:
            with props.suppress(hs, 'label'):
                hs.label = self.displayCtx.getDisplay(hs.overlay).name

        if canvas.smooth or self.plotType == 'centre':
            canvas.drawDataSeries(hss)

        # use a step plot when plotting bin edges
        else:
            canvas.drawDataSeries(hss, drawstyle='steps-pre')

        canvas.drawArtists()


    def createDataSeries(self, overlay):
        """Creates a :class:`.HistogramSeries` instance for the specified
        overlay.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        if isinstance(overlay, fslimage.Image):
            if overlay.iscomplex:
                hsType = histogramseries.ComplexHistogramSeries
            else:
                hsType = histogramseries.ImageHistogramSeries
        elif isinstance(overlay, fslmesh.Mesh):
            hsType = histogramseries.MeshHistogramSeries
        else:
            return None, None, None

        hs = hsType(overlay, self.overlayList, self.displayCtx, self.canvas)
        hs.colour      = self.getOverlayPlotColour(overlay)
        hs.lineStyle   = self.getOverlayPlotStyle(overlay)
        hs.lineWidth   = 2
        hs.alpha       = 1

        return hs, [], []


    def prepareDataSeries(self, hs):
        """Overrides :meth:`.PlotPanel.prepareDataSeries`.

        Performs some pre-processing on the data contained in the given
        :class:`.HistogramSeries` instance.
        """

        xdata, ydata = hs.getData()

        if xdata is None   or \
           ydata is None   or \
           len(xdata) == 0 or \
           len(ydata) == 0:
            return None, None

        # If smoothing is enabled, we just
        # need to provide the data as-is
        if self.canvas.smooth:
            xdata = np.array(xdata[:-1], dtype=np.float32)
            ydata = np.array(ydata,      dtype=np.float32)

        # If plotting on bin edges, we need to
        # munge the histogram data a bit so that
        # plt.plot(drawstyle='steps-pre') plots
        # it nicely.
        elif self.plotType == 'edge':
            xpad = np.zeros(len(xdata) + 1, dtype=np.float32)
            ypad = np.zeros(len(ydata) + 2, dtype=np.float32)

            xpad[ :-1] = xdata
            xpad[  -1] = xdata[-1]
            ypad[1:-1] = ydata
            xdata      = xpad
            ydata      = ypad

        # otherwise if plotting bin centres,
        # we need to offset the data, as it
        # is on bin edges
        elif self.plotType == 'centre':
            ydata = np.array(ydata,      dtype=np.float32)
            xdata = np.array(xdata[:-1], dtype=np.float32)
            xdata = xdata + 0.5 * (xdata[1] - xdata[0])

        # The passed-in series may just
        # be a DataSeries instance.
        if not isinstance(hs, histogramseries.HistogramSeries):
            return xdata, ydata

        # Or a HistogramSeries instance
        if self.histType == 'count':
            return xdata, ydata

        # Normalise by bin width to produce a
        # probability density function, so it
        # will look approximately the same,
        # regardless of the current nbins setting
        elif self.histType == 'probability':
            nvals = hs.numHistogramValues
            return xdata, ydata / (nvals * hs.binWidth)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.selectedOverlay` changes. Configures the
        :meth:`toggleHistogramOverlay` action.
        """

        overlay = self.displayCtx.getSelectedOverlay()
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
