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

import props

import fsl.data.image                             as fslimage
import fsl.data.strings                           as strings
import fsl.utils.dialog                           as fsldlg
import fsl.fsleyes.actions                        as actions
import fsl.fsleyes.plotting.histogramseries       as histogramseries
import fsl.fsleyes.controls.histogramcontrolpanel as histogramcontrolpanel
import fsl.fsleyes.controls.plotlistpanel         as plotlistpanel
import                                               plotpanel


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

       ~fsl.fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsl.fsleyes.controls.histogramcontrolpanel.HistogramControlPanel

    
    The following :mod:`actions` are provided, in addition to those already
    provided by the :class:`.PlotPanel`:

    .. autosummary::
       :nosignatures:
   
       toggleHistogramList
       toggleHistogramControl

    
    The ``PlotListPanel`` and ``HistogramControlPanel`` are both shown
    by default when a new ``HistogramPanel`` is created.
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


    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``HistogramPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        plotpanel.OverlayPlotPanel.__init__(
            self, parent, overlayList, displayCtx)

        self.addListener('histType', self._name, self.draw)

        def addPanels():
            self.toggleHistogramControl()
            self.toggleHistogramList()

        wx.CallAfter(addPanels) 


    def destroy(self):
        """Removes some property listeners, and calls
        :meth:`.PlotPanel.destroy`.
        """
        
        self.removeListener('histType', self._name)
        
        plotpanel.OverlayPlotPanel.destroy(self)

        
    @actions.toggleAction
    def toggleHistogramList(self):
        """Shows/hides a :class:`.PlotListPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(plotlistpanel.PlotListPanel, self, location=wx.TOP)

        
    @actions.toggleAction
    def toggleHistogramControl(self):
        """Shows/hides a :class:`.HistogramControlPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(
            histogramcontrolpanel.HistogramControlPanel,
            self,
            location=wx.TOP) 

        
    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Passes some
        :class:`.HistogramSeries` instances to the
        :meth:`.PlotPanel.drawDataSeries` method.
        """        

        if self.showMode == 'all':
            overlays = self._overlayList[:]
            
        elif self.showMode == 'current':
            overlays = [self._displayCtx.getSelectedOverlay()]
            
        else:
            overlays = []

        hss = [self.getDataSeries(o) for o in overlays]
        hss = [hs for hs in hss if hs is not None]

        for hs in hss:
            hs.label = self._displayCtx.getDisplay(hs.overlay).name

        if self.smooth:
            self.drawDataSeries(hss,
                                preproc=self.__prepareHistogramSeries)
        else:
            self.drawDataSeries(hss,
                                preproc=self.__prepareHistogramSeries,
                                drawstyle='steps-pre')


    def createDataSeries(self, overlay):
        """Creates a :class:`.HistogramSeries` instance for the specified
        overlay.
        """

        if not isinstance(overlay, fslimage.Image):
            return None, None, None


        # We are creating a new HS instance, so it
        # needs to do some initla data range/histogram
        # calculations. Show a message while this is
        # happening. 
        def loadHs():
            return histogramseries.HistogramSeries(overlay,
                                                   self._displayCtx,
                                                   self._overlayList)

        hs = fsldlg.ProcessingDialog(
            None,
            strings.messages[self, 'calcHist'].format(overlay.name),
            loadHs).Run()
        
        hs.colour      = self.getOverlayPlotColour(overlay)
        hs.alpha       = 1
        hs.lineWidth   = 1
        hs.lineStyle   = '-'

        return hs, [], []


    def __prepareHistogramSeries(self, hs):
        """Performs some pre-processing on the data contained in the given
        :class:`.HistogramSeries` instance. This method is used as the
        ``preproc`` argument to the :meth:`.PlotPanel.drawDataSeries` method.
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
