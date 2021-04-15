#!/usr/bin/env python
#
# addroihistogram.py - The AddROIHistogramAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AddROIHistogramAction` class, an
action used by the :class:`.HistogramPanel`.
"""


import          wx
import numpy as np

import fsl.data.image                          as fslimage
import fsleyes.views.histogrampanel            as histogrampanel
import fsleyes.strings                         as strings
import fsleyes.plotting.dataseries             as dataseries
import fsleyes.plotting.histogramseries        as histogramseries
import fsleyes.plugins.tools.addmaskdataseries as addmaskdataseries
import fsleyes.actions.base                    as base



class AddROIHistogramAction(base.Action):
    """The ``AddROIHistogramAction`` class is used by the
    :class:`.HistogramPanel`.

    It performs a very similar task to the :class:`.AddMaskDataSeriesAction` -
    the user selects a binary mask, the data within the base image is extracted
    for that mask, and the histogram of that data is added to the plot.
    """


    @staticmethod
    def supportedViews():
        """The ``AddROIHistogramAction`` is restricted for use with the
        :class:`.HistogramPanel`.
        """
        return [histogrampanel.HistogramPanel]


    def __init__(self, overlayList, displayCtx, plotPanel):
        """Create an ``AddROIHistogramAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg plotPanel:   The :class:`.HistogramPanel`.
        """

        base.Action.__init__(
            self, overlayList, displayCtx, self.__addROIHistogram)

        self.__plotPanel  = plotPanel
        self.__roiOptions = []

        overlayList.addListener('overlays',
                                self.name,
                                self.__overlayListChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__overlayListChanged)

        self.__overlayListChanged()


    def destroy(self):
        """Must be called when this ``AddROIHistogramAction`` is no
        longer in use.
        """
        if self.destroyed:
            return
        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.__plotPanel  = None
        self.__roiOptions = None
        base.Action.destroy(self)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.selectedOverlay` changes. Updates a list of
        valid mask images for the currently selected overlay.
        """

        overlay = self.displayCtx.getSelectedOverlay()

        if (len(self.overlayList) == 0 or
           (not isinstance(overlay, fslimage.Image))):
            self.enabled = False
            return

        self.__roiOptions = [o for o in self.overlayList if
                             isinstance(o, fslimage.Image) and
                             o is not overlay              and
                             o.sameSpace(overlay)]

        self.enabled = len(self.__roiOptions)  > 0



    def __addROIHistogram(self):
        """Prompts the user to select an ROI mask, calculates the histogram
        of that mask on the currently selected overlay, and adds the result
        to the ``HistogramPanel``.
        """

        overlay    = self.displayCtx.getSelectedOverlay()
        opts       = self.displayCtx.getOpts(overlay)
        roiOptions = self.__roiOptions

        frame   = wx.GetApp().GetTopWindow()
        msg     = strings.messages[self, 'selectMask'].format(overlay.name)
        title   = strings.titles[  self, 'selectMask'].format(overlay.name)

        dlg = addmaskdataseries.MaskDialog(
            frame,
            [o.name for o in roiOptions],
            title=title,
            message=msg,
            checkbox=False)

        if dlg.ShowModal() != wx.ID_OK:
            return

        maskimg = roiOptions[dlg.GetChoice()]
        mask    = maskimg[:] > 0

        if overlay.ndim > 3: data = overlay[opts.index()][mask]
        else:                data = overlay[mask]

        count           = self.__plotPanel.histType == 'count'
        drange          = (np.nanmin(data), np.nanmax(data))
        nbins           = histogramseries.autoBin(data, drange)
        xdata, ydata, _ = histogramseries.histogram(data,
                                                    nbins,
                                                    drange,
                                                    drange,
                                                    includeOutliers=False,
                                                    count=count)

        ds           = dataseries.DataSeries(overlay,
                                             self.overlayList,
                                             self.displayCtx,
                                             self.__plotPanel)
        ds.colour    = self.__plotPanel.getOverlayPlotColour(overlay)
        ds.lineStyle = self.__plotPanel.getOverlayPlotStyle(overlay)
        ds.lineWidth = 2
        ds.alpha     = 1
        ds.label     = '{} [mask: {}]'.format(overlay.name, maskimg.name)

        # We have to run the data through
        # prepareDataSeries to preprocess
        # (e.g. smooth) it
        ds.setData(xdata, ydata)
        ds.setData(*self.__plotPanel.prepareDataSeries(ds))

        self.__plotPanel.canvas.dataSeries.append(ds)
