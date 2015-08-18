#!/usr/bin/env python
#
# histogrampanel.py - A panel which plots a histogram for the data from the
#                     currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import numpy as np

import props

import fsl.data.image         as fslimage
import fsl.data.strings       as strings
import fsl.utils.dialog       as fsldlg
import fsl.fsleyes.controls   as fslcontrols
import                           plotpanel


log = logging.getLogger(__name__)

        
def autoBin(data, dataRange):

    # Automatic histogram bin calculation
    # as implemented in the original FSLView

    dMin, dMax = dataRange
    dRange     = dMax - dMin

    binSize = np.power(10, np.ceil(np.log10(dRange) - 1) - 1)

    nbins = dRange / binSize
    
    while nbins < 100:
        binSize /= 2
        nbins    = dRange / binSize

    if issubclass(data.dtype.type, np.integer):
        binSize = max(1, np.ceil(binSize))

    adjMin = np.floor(dMin / binSize) * binSize
    adjMax = np.ceil( dMax / binSize) * binSize

    nbins = int((adjMax - adjMin) / binSize) + 1

    return nbins


class HistogramSeries(plotpanel.DataSeries):

    nbins           = props.Int(minval=10,
                                maxval=500,
                                default=100,
                                clamped=True)
    ignoreZeros     = props.Boolean(default=True)
    showOverlay     = props.Boolean(default=False)
    includeOutliers = props.Boolean(default=False)
    volume          = props.Int(minval=0, maxval=0, clamped=True)
    dataRange       = props.Bounds(
        ndims=1,
        labels=[strings.choices['HistogramPanel.dataRange.min'],
                strings.choices['HistogramPanel.dataRange.max']])


    def __init__(self,
                 overlay,
                 hsPanel,
                 displayCtx,
                 overlayList,
                 volume=0,
                 baseHs=None):

        log.debug('New HistogramSeries instance for {} '
                  '(based on existing instance: {})'.format(
                      overlay.name, baseHs is not None)) 

        plotpanel.DataSeries.__init__(self, overlay)
        self.hsPanel     = hsPanel
        self.name        = '{}_{}'.format(type(self).__name__, id(self))
        self.volume      = volume

        self.displayCtx  = displayCtx
        self.overlayList = overlayList
        self.overlay3D   = None

        if overlay.is4DImage():
            self.setConstraint('volume', 'maxval', overlay.shape[3] - 1)

        if baseHs is not None:
            self.dataRange.xmin     = baseHs.dataRange.xmin
            self.dataRange.xmax     = baseHs.dataRange.xmax
            self.dataRange.x        = baseHs.dataRange.x
            self.nbins              = baseHs.nbins
            self.volume             = baseHs.volume
            self.ignoreZeros        = baseHs.ignoreZeros
            self.includeOutliers    = baseHs.includeOutliers
            self.nvals              = baseHs.nvals
            self.xdata              = np.array(baseHs.xdata)
            self.ydata              = np.array(baseHs.ydata)
            self.finiteData         = np.array(baseHs.finiteData)
            self.nonZeroData        = np.array(baseHs.nonZeroData)
            self.clippedFiniteData  = np.array(baseHs.finiteData)
            self.clippedNonZeroData = np.array(baseHs.nonZeroData) 
 
        else:
            self.initProperties()
        
        overlayList.addListener('overlays', self.name, self.overlaysChanged)

        self.addListener('volume',          self.name, self.volumeChanged)
        self.addListener('dataRange',       self.name, self.dataRangeChanged)
        self.addListener('nbins',           self.name, self.histPropsChanged)
        self.addListener('ignoreZeros',     self.name, self.histPropsChanged)
        self.addListener('includeOutliers', self.name, self.histPropsChanged)
        self.addListener('showOverlay',     self.name, self.showOverlayChanged)

        
    def initProperties(self):

        log.debug('Performining initial histogram '
                  'calculations for overlay {}'.format(
                      self.overlay.name))

        data  = self.overlay.data[:]
        
        finData = data[np.isfinite(data)]
        dmin    = finData.min()
        dmax    = finData.max()
        dist    = (dmax - dmin) / 10000.0
        
        nzData = finData[finData != 0]
        nzmin  = nzData.min()
        nzmax  = nzData.max()

        self.dataRange.xmin = dmin
        self.dataRange.xmax = dmax  + dist
        self.dataRange.xlo  = nzmin
        self.dataRange.xhi  = nzmax + dist

        self.nbins = autoBin(nzData, self.dataRange.x)

        if not self.overlay.is4DImage():
            self.finiteData  = finData
            self.nonZeroData = nzData
            self.dataRangeChanged(callHistPropsChanged=False)
        else:
            self.volumeChanged(callHistPropsChanged=False)

        self.histPropsChanged()

        
    def volumeChanged(
            self,
            ctx=None,
            value=None,
            valid=None,
            name=None,
            callHistPropsChanged=True):

        if self.overlay.is4DImage(): data = self.overlay.data[..., self.volume]
        else:                        data = self.overlay.data[:]

        data = data[np.isfinite(data)]

        self.finiteData  = data
        self.nonZeroData = data[data != 0]

        self.dataRangeChanged(callHistPropsChanged=False)

        if callHistPropsChanged:
            self.histPropsChanged()


    def dataRangeChanged(
            self,
            ctx=None,
            value=None,
            valid=None,
            name=None,
            callHistPropsChanged=True):
        finData = self.finiteData
        nzData  = self.nonZeroData
        
        self.clippedFiniteData  = finData[(finData >= self.dataRange.xlo) &
                                          (finData <  self.dataRange.xhi)]
        self.clippedNonZeroData = nzData[ (nzData  >= self.dataRange.xlo) &
                                          (nzData  <  self.dataRange.xhi)]

        if callHistPropsChanged:
            self.histPropsChanged()

        
    def destroy(self):
        """This needs to be called when this ``HistogramSeries`` instance
        is no longer being used.
        """
        self            .removeListener('nbins',           self.name)
        self            .removeListener('ignoreZeros',     self.name)
        self            .removeListener('includeOutliers', self.name)
        self            .removeListener('volume',          self.name)
        self            .removeListener('dataRange',       self.name)
        self            .removeListener('nbins',           self.name)
        self.overlayList.removeListener('overlays',        self.name)
        
        if self.overlay3D is not None:
            self.overlayList.remove(self.overlay3D)
            self.overlay3D = None

    
    def histPropsChanged(self, *a):

        log.debug('Calculating histogram for '
                  'overlay {}'.format(self.overlay.name))

        if self.dataRange.xhi - self.dataRange.xlo < 0.00000001:
            self.xdata = np.array([])
            self.ydata = np.array([])
            self.nvals = 0
            return

        if self.ignoreZeros:
            if self.includeOutliers: data = self.nonZeroData
            else:                    data = self.clippedNonZeroData
        else:
            if self.includeOutliers: data = self.finiteData
            else:                    data = self.clippedFiniteData 
        
        if self.hsPanel.autoBin:
            nbins = autoBin(data, self.dataRange.x)

            self.disableListener('nbins', self.name)
            self.nbins = nbins
            self.enableListener('nbins', self.name)

        # Calculate bin edges
        bins = np.linspace(self.dataRange.xlo,
                           self.dataRange.xhi,
                           self.nbins + 1)

        if self.includeOutliers:
            bins[ 0] = self.dataRange.xmin
            bins[-1] = self.dataRange.xmax
            
        # Calculate the histogram
        histX    = bins
        histY, _ = np.histogram(data.flat, bins=bins)
            
        self.xdata = histX
        self.ydata = histY
        self.nvals = histY.sum()

        log.debug('Calculated histogram for overlay '
                  '{} (number of values: {}, number '
                  'of bins: {})'.format(
                      self.overlay.name,
                      self.nvals,
                      self.nbins))


    def showOverlayChanged(self, *a):

        if not self.showOverlay:
            if self.overlay3D is not None:

                log.debug('Removing 3D histogram overlay mask for {}'.format(
                    self.overlay.name))
                self.overlayList.remove(self.overlay3D)
                self.overlay3D = None

        else:

            log.debug('Creating 3D histogram overlay mask for {}'.format(
                self.overlay.name))
            
            self.overlay3D = fslimage.Image(
                self.overlay.data,
                name='{}/histogram/mask'.format(self.overlay.name),
                header=self.overlay.nibImage.get_header())

            self.overlayList.append(self.overlay3D)

            opts = self.displayCtx.getOpts(self.overlay3D, overlayType='mask')

            opts.bindProps('volume',    self)
            opts.bindProps('colour',    self)
            opts.bindProps('threshold', self, 'dataRange')


    def overlaysChanged(self, *a):
        
        if self.overlay3D is None:
            return

        # If a 3D overlay was being shown, and it
        # has been removed from the overlay list
        # by the user, turn the showOverlay property
        # off
        if self.overlay3D not in self.overlayList:
            
            self.disableListener('showOverlay', self.name)
            self.showOverlay = False
            self.showOverlayChanged()
            self.enableListener('showOverlay', self.name)


    def getData(self):

        if len(self.xdata) == 0 or \
           len(self.ydata) == 0:
            return self.xdata, self.ydata

        # If smoothing is not enabled, we'll
        # munge the histogram data a bit so
        # that plt.plot(drawstyle='steps-pre')
        # plots it nicely.
        if not self.hsPanel.smooth:

            xdata = np.zeros(len(self.xdata) + 1, dtype=np.float32)
            ydata = np.zeros(len(self.ydata) + 2, dtype=np.float32)

            xdata[ :-1] = self.xdata
            xdata[  -1] = self.xdata[-1]
            ydata[1:-1] = self.ydata


        # If smoothing is enabled, the above munge
        # is not necessary, and will probably cause
        # the spline interpolation to fail
        else:
            xdata = np.array(self.xdata[:-1], dtype=np.float32)
            ydata = np.array(self.ydata,      dtype=np.float32)

        nvals    = self.nvals
        histType = self.hsPanel.histType
            
        if   histType == 'count':       return xdata, ydata
        elif histType == 'probability': return xdata, ydata / nvals

    
class HistogramPanel(plotpanel.PlotPanel):


    autoBin     = props.Boolean(default=True)
    showCurrent = props.Boolean(default=True)
    histType    = props.Choice(
        ('probability', 'count'),
        labels=[strings.choices['HistogramPanel.histType.probability'],
                strings.choices['HistogramPanel.histType.count']])

    selectedSeries = props.Int(minval=0, clamped=True)
    

    def __init__(self, parent, overlayList, displayCtx):

        actionz = {
            'toggleHistogramList'    : self.toggleHistogramList,
            'toggleHistogramControl' : lambda *a: self.togglePanel(
                fslcontrols.HistogramControlPanel, self, location=wx.TOP) 
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = self.getFigure()
        
        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__overlaysChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)

        self.addListener('showCurrent', self._name, self.draw)
        self.addListener('histType',    self._name, self.draw)
        self.addListener('autoBin',     self._name, self.__autoBinChanged)
        self.addListener('dataSeries',  self._name, self.__dataSeriesChanged)

        self.__histCache = {}
        self.__current   = None
        self.__updateCurrent()

        self.Layout()


    def toggleHistogramList(self, *a):
        self.togglePanel(fslcontrols.HistogramListPanel, self, location=wx.TOP)

        panel = self.getPanel(fslcontrols.HistogramListPanel)

        if panel is None:
            return

        def listSelect(ev):
            ev.Skip()
            self.selectedSeries = panel.GetSelection()


    def destroy(self):
        """De-registers property listeners. """
        
        self.removeListener('showCurrent', self._name)
        self.removeListener('histType',    self._name)
        self.removeListener('autoBin',     self._name)
        self.removeListener('dataSeries',  self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        for hs in set(self.dataSeries[:] + self.__histCache.values()):
            hs.destroy()

        plotpanel.PlotPanel.destroy(self)


    def __dataSeriesChanged(self, *a):
        self.setConstraint('selectedSeries',
                           'maxval',
                           len(self.dataSeries) - 1)

        listPanel = self.getPanel(fslcontrols.HistogramListPanel)

        if listPanel is None:
            self.selectedSeries = 0
        else:
            self.selectedSeries = listPanel.getListBox().GetSelection()

            
    def __overlaysChanged(self, *a):
        
        self.disableListener('dataSeries', self._name)
        
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
                
        self.enableListener('dataSeries', self._name)

        # Remove any dead overlays
        # from the histogram cache
        for overlay in list(self.__histCache.keys()):
            if overlay not in self._overlayList:
                log.debug('Removing cached histogram series '
                          'for overlay {}'.format(overlay.name))
                hs = self.__histCache.pop(overlay)
                hs.destroy()
        
        self.__selectedOverlayChanged()

        
    def __selectedOverlayChanged(self, *a):

        self.__updateCurrent()
        self.draw()

        
    def __autoBinChanged(self, *a):
        """Called when the :attr:`autoBin` property changes. Makes sure that
        all existing :class:`HistogramSeries` instances are updated before
        the plot is refreshed.
        """

        for ds in self.dataSeries:
            ds.histPropsChanged()

        if self.__current is not None:
            self.__current.histPropsChanged()

        self.draw()
        

    def __updateCurrent(self):

        # Make sure that the previous HistogramSeries
        # cleans up after itself, unless it has been
        # cached
        if self.__current is not None and \
           self.__current not in self.__histCache.values():
            self.__current.destroy()
            
        self.__current = None
        overlay        = self._displayCtx.getSelectedOverlay()

        if len(self._overlayList) == 0 or \
           not isinstance(overlay, fslimage.Image):
            return

        # See if there is already a HistogramSeries based on the
        # current overlay - if there is, use it as the 'base' HS
        # for the new one, as it will save us some processing time
        if overlay in self.__histCache:
            log.debug('Creating new histogram series for overlay {} '
                      'from cached copy'.format(overlay.name))
            baseHs = self.__histCache[overlay]
        else:
            baseHs = None

        def loadHs():
            return HistogramSeries(overlay,
                                   self,
                                   self._displayCtx,
                                   self._overlayList,
                                   baseHs=baseHs)

        # We are creating a new HS instance, so it
        # needs to do some initla data range/histogram
        # calculations. Show a message while this is
        # happening.
        if baseHs is None:
            hs = fsldlg.ProcessingDialog(
                None,
                strings.messages[self, 'calcHist'].format(overlay.name),
                loadHs).Run()

            # Put the initial HS instance for this
            # overlay in the cache so we don't have
            # to re-calculate it later
            log.debug('Caching histogram series for '
                      'overlay {}'.format(overlay.name))
            self.__histCache[overlay] = hs
            
        # The new HS instance is being based on the
        # current instance, so it can just copy the
        # histogram data over - no message dialog
        # is needed
        else:
            hs = loadHs()

        hs.colour      = [0, 0, 0]
        hs.alpha       = 1
        hs.lineWidth   = 1
        hs.lineStyle   = '-'
        hs.label       = None

        self.__current = hs


    def getCurrent(self):
        if self.__current is None:
            self.__updateCurrent()

        if self.__current is None:
            return None

        return HistogramSeries(self.__current.overlay,
                               self,
                               self._displayCtx,
                               self._overlayList,
                               baseHs=self.__current) 


    def draw(self, *a):

        extra = None

        if self.showCurrent:
            
            if self.__current is not None:
                extra = [self.__current]

        if self.smooth: self.drawDataSeries(extra)
        else:           self.drawDataSeries(extra, drawstyle='steps-pre')
