#!/usr/bin/env python
#
# histogrampanel.py - The HistogramPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramPanel`, which is a *FSLeyes view*
that plots the histogram of data from :class:`.Image` overlays.  A
``HistogramPanel`` looks something like this:

.. image:: images/histogrampanel.png
   :scale: 50%
   :align: center


``HistogramPanel`` instances use the :class:`HistogramSeries` class (a
:class:`.DataSeries` sub-class) to encapsulate histogram data.
"""


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


class HistogramPanel(plotpanel.PlotPanel):
    """A :class:`.PlotPanel` which plots histograms from :class:`.Image`
    overlay data.

    A ``HistogramPanel`` plots one or more :class:`HistogramSeries` instances,
    each of which encapsulate histogram data from an :class:`.Image` overlay.

    In a similar manner to the :class:`.TimeSeriesPanel` a ``HistogramPanel``
    will, by default, plot a histogram from the currently selected overlay
    (dictated by the :attr:`.DisplayContext.selectedOverlay` property), if it
    is an :class:`.Image` instance.  This histogram series is referred to as
    the *current* histogram, and it can be enabled/disabled with the
    :attr:`showCurrent` setting.


    A couple of control panels may be shown on a ``HistogramPanel``:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.controls.histogramlistpanel.HistogramListPanel
       ~fsl.fsleyes.controls.histogramcontrolpanel.HistogramControlPanel

    The following actions are provided, in addition to those already provided
    by the :class:`.PlotPanel`:

    ========================== ============================================
    ``toggleHistogramList``    Show/hide a :class:`.HistogramListPanel`.
    ``toggleHistogramControl`` Show/hide a :class:`.HistogramControlPanel`.
    ========================== ============================================

    The ``HistogramListPanel`` and ``HistogramControlPanel`` are both shown
    by default when a new ``HistogramPanel`` is created.
    """


    autoBin = props.Boolean(default=True)
    """If ``True``, the number of bins used for each :class:`HistogramSeries`
    is calculated automatically. Otherwise, :attr:`HistogramSeries.nbins` bins
    are used.
    """

    
    showCurrent = props.Boolean(default=True)
    """If ``True``, a histogram for the currently selected overlay (if it is
    an :class:`.Image` instance) is always plotted.
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

    
    selectedSeries = props.Int(minval=0, clamped=True)
    """The currently selected :class:`HistogramSeries` - an index into the
    :attr:`.PlotPanel.dataSeries` list.

    This property is used by the :class:`.HistogramListPanel` and the
    :class:`.HistogramControlPanel`, to allow the user to change the settings
    of individual :class:`HistogramSeries` instances. 
    """
    

    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``HistogramPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

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
                                      self.__overlayListChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)

        self.addListener('showCurrent', self._name, self.draw)
        self.addListener('histType',    self._name, self.draw)
        self.addListener('autoBin',     self._name, self.__autoBinChanged)
        self.addListener('dataSeries',  self._name, self.__dataSeriesChanged)

        # Creating a HistogramSeries is a bit expensive
        # as it needs to, well, create a histogram. So
        # we only create one HistogramSeries per overlay,
        # and we cache them here so that the user only
        # has to wait the first time they select an
        # overlay for its histogram to be calculated.
        #
        # When a HistogramSeries is added to the dataSeries
        # list, it is copied from the cached one so, again,
        # the histogram calculation doesn't need to be done.
        self.__histCache = {}
        self.__current   = None
        self.__updateCurrent()

        def addPanels():
            self.run('toggleHistogramControl') 
            self.run('toggleHistogramList')

        wx.CallAfter(addPanels) 


    def destroy(self):
        """Removes some property listeners, destroys all existing
        :class:`HistogramSeries` instances, and calls
        :meth:`.PlotPanel.destroy`.
        """
        
        self.removeListener('showCurrent', self._name)
        self.removeListener('histType',    self._name)
        self.removeListener('autoBin',     self._name)
        self.removeListener('dataSeries',  self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        for hs in set(self.dataSeries[:] + self.__histCache.values()):
            hs.destroy()

        plotpanel.PlotPanel.destroy(self)


    def getCurrent(self):
        """Return the :class:`HistogramSeries` instance for the currently
        selected overlay. Returns ``None`` if :attr:`showCurrent` is
        ``False``, or the current overlay is not an :class:`.Image`.
        """
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
        """Draws the current :class:`HistogramSeries` if there is one,, and
        any ``HistogramSeries`` that are in the :attr:`.PlotPanel.dataSeries`
        list, via a call to :meth:`.PlotPanel.drawDataSeries`.
        """

        extra = None

        if self.showCurrent:
            
            if self.__current is not None:
                extra = [self.__current]

        if self.smooth: self.drawDataSeries(extra)
        else:           self.drawDataSeries(extra, drawstyle='steps-pre')


    def toggleHistogramList(self, *a):
        """Shows/hides a :class:`.HistogramListPanel`. See the
        :meth:`.ViewPanel.togglePanel` method.
        """
        self.togglePanel(fslcontrols.HistogramListPanel, self, location=wx.TOP)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`.PlotPanel.dataSeries` property changes.

        Updates the :attr:`selectedSeries` property accordingly.
        """
        self.setConstraint('selectedSeries',
                           'maxval',
                           len(self.dataSeries) - 1)

        listPanel = self.getPanel(fslcontrols.HistogramListPanel)

        if listPanel is None:
            self.selectedSeries = 0
        else:
            self.selectedSeries = listPanel.getListBox().GetSelection()

            
    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        Removes any :class:`HistogramSeries` from the
        :attr:`.PlotPanel.dataSeries` list which correspond to overlays that
        no longer exist.
        """
        
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
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.

        Updates the current :class:`HistogramSeries`.
        """

        self.__updateCurrent()
        self.draw()

        
    def __autoBinChanged(self, *a):
        """Called when the :attr:`autoBin` property changes. Makes sure that
        all existing :class:`HistogramSeries` instances are updated before
        the plot is refreshed.
        """

        for ds in self.dataSeries:
            ds.update()

        if self.__current is not None:
            self.__current.update()

        self.draw()
        

    def __updateCurrent(self):
        """Creates/updates the current :class:`HistogramSeries` instance,
        if necessary.
        """

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


class HistogramSeries(plotpanel.DataSeries):
    """A ``HistogramSeries`` generates histogram data from an :class:`.Image`
    instance.
    """

    nbins = props.Int(minval=10, maxval=500, default=100, clamped=True)
    """Number of bins to use in the histogram. This value is overridden
    by the :attr:`HistogramPanel.autoBin` setting.

    .. note:: I'm not sure why ``autoBin`` is a :class:`HistogramPanel`
              setting, rather than a ``HistogramSeries`` setting. I might 
              change this some time.
    """

    
    ignoreZeros = props.Boolean(default=True)
    """If ``True``, zeros are excluded from the calculated histogram. """

    
    showOverlay = props.Boolean(default=False)
    """If ``True``, a 3D mask :class:`.Image` overlay is added to the
    :class:`.OverlayList`, which highlights the voxels that have been included
    in the histogram.
    """


    includeOutliers = props.Boolean(default=False)
    """If ``True``, values which are outside of the :attr:`dataRange` are
    included in the histogram end bins.
    """

    
    volume = props.Int(minval=0, maxval=0, clamped=True)
    """If the :class:`.Image` overlay associated with this ``HistogramSeries`` 
    is 4D, this settings specifies the index of the volume that the histogram
    is calculated upon.

    .. note:: Calculating the histogram over an entire 4D :class:`.Image` is
              not yet supported.
    """

    
    dataRange = props.Bounds(ndims=1)
    """Specifies the range of data which should be included in the histogram.
    See the :attr:`includeOutliers` property.
    """


    def __init__(self,
                 overlay,
                 hsPanel,
                 displayCtx,
                 overlayList,
                 volume=0,
                 baseHs=None):
        """Create a ``HistogramSeries``.

        :arg overlay:     The :class:`.Image` overlay to calculate a histogram
                          for.
        
        :arg hsPanel:     The :class:`HistogramPanel` that is displaying this
                          ``HistogramSeries``.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg overlayList: The :class:`.OverlayList` instance.
        
        :arg volume:      If the ``overlay`` is 4D, the initial value for the
                          :attr:`volume` property.
        
        :arg baseHs:      If a ``HistogramSeries`` has already been created
                          for the ``overlay``, it may be passed in here, so
                          that the histogram data can be copied instead of
                          having to be re-calculated.
        """

        log.debug('New HistogramSeries instance for {} '
                  '(based on existing instance: {})'.format(
                      overlay.name, baseHs is not None)) 

        plotpanel.DataSeries.__init__(self, overlay)

        self.volume        = volume
        self.__hsPanel     = hsPanel
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__overlay3D   = None

        if overlay.is4DImage():
            self.setConstraint('volume', 'maxval', overlay.shape[3] - 1)

        # If we have a baseHS, we 
        # can copy all its data
        if baseHs is not None:
            self.dataRange.xmin     = baseHs.dataRange.xmin
            self.dataRange.xmax     = baseHs.dataRange.xmax
            self.dataRange.x        = baseHs.dataRange.x
            self.nbins              = baseHs.nbins
            self.volume             = baseHs.volume
            self.ignoreZeros        = baseHs.ignoreZeros
            self.includeOutliers    = baseHs.includeOutliers
            
            self.__nvals              =          baseHs.__nvals
            self.__xdata              = np.array(baseHs.__xdata)
            self.__ydata              = np.array(baseHs.__ydata)
            self.__finiteData         = np.array(baseHs.__finiteData)
            self.__nonZeroData        = np.array(baseHs.__nonZeroData)
            self.__clippedFiniteData  = np.array(baseHs.__finiteData)
            self.__clippedNonZeroData = np.array(baseHs.__nonZeroData) 

        # Otherwise we need to calculate
        # it all for ourselves
        else:
            self.__initProperties()
        
        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        self       .addListener('volume',
                                self.__name,
                                self.__volumeChanged)
        self       .addListener('dataRange',
                                self.__name,
                                self.__dataRangeChanged)
        self       .addListener('nbins',
                                self.__name,
                                self.__histPropsChanged)
        self       .addListener('ignoreZeros',
                                self.__name,
                                self.__histPropsChanged)
        self       .addListener('includeOutliers',
                                self.__name,
                                self.__histPropsChanged)
        self       .addListener('showOverlay',
                                self.__name,
                                self.__showOverlayChanged)

        
    def update(self):
        """This method may be called to force re-calculation of the
        histogram data.
        """
        self.__histPropsChanged()

        
    def destroy(self):
        """This needs to be called when this ``HistogramSeries`` instance
        is no longer being used.

        It removes several property listeners and, if the :attr:`overlay3D`
        property is ``True``, removes the mask overlay from the
        :class:`.OverlayList`.
        """
        self              .removeListener('nbins',           self.__name)
        self              .removeListener('ignoreZeros',     self.__name)
        self              .removeListener('includeOutliers', self.__name)
        self              .removeListener('volume',          self.__name)
        self              .removeListener('dataRange',       self.__name)
        self              .removeListener('nbins',           self.__name)
        self.__overlayList.removeListener('overlays',        self.__name)
        
        if self.__overlay3D is not None:
            self.__overlayList.remove(self.__overlay3D)
            self.__overlay3D = None

        
    def __initProperties(self):
        """Called by :meth:`__init__`. Calculates and caches some things which
        are needed for the histogram calculation.

        .. note:: This method is never called if a ``baseHs`` is provided to
                 :meth:`__init__`.
        """

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

        self.nbins = self.__autoBin(nzData, self.dataRange.x)

        if not self.overlay.is4DImage():
            
            self.__finiteData  = finData
            self.__nonZeroData = nzData
            self.__dataRangeChanged(callHistPropsChanged=False)
            
        else:
            self.__volumeChanged(callHistPropsChanged=False)

        self.__histPropsChanged()

        
    def __volumeChanged(
            self,
            ctx=None,
            value=None,
            valid=None,
            name=None,
            callHistPropsChanged=True):
        """Called when the :attr:`volume` property changes, and also by the
        :meth:`__initProperties` method.

        Re-calculates some things for the new overlay volume.

        :arg callHistPropsChanged: If ``True`` (the default), the
                                   :meth:`__histPropsChanged` method will be
                                   called.

        All other arguments are ignored, but are passed in when this method is
        called due to a property change (see the
        :meth:`.HasProperties.addListener` method).        
        """

        if self.overlay.is4DImage(): data = self.overlay.data[..., self.volume]
        else:                        data = self.overlay.data[:]

        data = data[np.isfinite(data)]

        self.__finiteData  = data
        self.__nonZeroData = data[data != 0]

        self.__dataRangeChanged(callHistPropsChanged=False)

        if callHistPropsChanged:
            self.__histPropsChanged()


    def __dataRangeChanged(
            self,
            ctx=None,
            value=None,
            valid=None,
            name=None,
            callHistPropsChanged=True):
        """Called when the :attr:`dataRange` property changes, and also by the
        :meth:`__initProperties` and :meth:`__volumeChanged` methods.

        :arg callHistPropsChanged: If ``True`` (the default), the
                                   :meth:`__histPropsChanged` method will be
                                   called.

        All other arguments are ignored, but are passed in when this method is
        called due to a property change (see the
        :meth:`.HasProperties.addListener` method).
        """
        finData = self.__finiteData
        nzData  = self.__nonZeroData
        
        self.__clippedFiniteData  = finData[(finData >= self.dataRange.xlo) &
                                            (finData <  self.dataRange.xhi)]
        self.__clippedNonZeroData = nzData[ (nzData  >= self.dataRange.xlo) &
                                            (nzData  <  self.dataRange.xhi)]

        if callHistPropsChanged:
            self.__histPropsChanged()

            
    def __histPropsChanged(self, *a):
        """Called internally, and when any histogram settings change.
        Re-calculates the histogram data.
        """

        log.debug('Calculating histogram for '
                  'overlay {}'.format(self.overlay.name))

        if self.dataRange.xhi - self.dataRange.xlo < 0.00000001:
            self.__xdata = np.array([])
            self.__ydata = np.array([])
            self.__nvals = 0
            return

        if self.ignoreZeros:
            if self.includeOutliers: data = self.__nonZeroData
            else:                    data = self.__clippedNonZeroData
        else:
            if self.includeOutliers: data = self.__finiteData
            else:                    data = self.__clippedFiniteData 
        
        if self.__hsPanel.autoBin:
            nbins = self.__autoBin(data, self.dataRange.x)

            self.disableListener('nbins', self.__name)
            self.nbins = nbins
            self.enableListener('nbins', self.__name)

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
            
        self.__xdata = histX
        self.__ydata = histY
        self.__nvals = histY.sum()

        log.debug('Calculated histogram for overlay '
                  '{} (number of values: {}, number '
                  'of bins: {})'.format(
                      self.overlay.name,
                      self.__nvals,
                      self.nbins))


    def __showOverlayChanged(self, *a):
        """Called when the :attr:`showOverlay` property changes.

        Adds/removes a 3D mask :class:`.Image` to the :class:`.OverlayList`,
        which highlights the voxels that have been included in the histogram.
        The :class:`.MaskOpts.threshold` property is bound to the
        :attr:`dataRange` property, so the masked voxels are updated whenever
        the histogram data range changes, and vice versa.
        """

        if not self.showOverlay:
            if self.__overlay3D is not None:

                log.debug('Removing 3D histogram overlay mask for {}'.format(
                    self.overlay.name))
                self.__overlayList.remove(self.__overlay3D)
                self.__overlay3D = None

        else:

            log.debug('Creating 3D histogram overlay mask for {}'.format(
                self.overlay.name))
            
            self.__overlay3D = fslimage.Image(
                self.overlay.data,
                name='{}/histogram/mask'.format(self.overlay.name),
                header=self.overlay.nibImage.get_header())

            self.__overlayList.append(self.__overlay3D)

            opts = self.__displayCtx.getOpts(self.__overlay3D,
                                             overlayType='mask')

            opts.bindProps('volume',    self)
            opts.bindProps('colour',    self)
            opts.bindProps('threshold', self, 'dataRange')


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        If a 3D mask overlay was being shown, and it has been removed from the
        ``OverlayList``, the :attr:`showOverlay` property is updated
        accordingly.
        """
        
        if self.__overlay3D is None:
            return

        # If a 3D overlay was being shown, and it
        # has been removed from the overlay list
        # by the user, turn the showOverlay property
        # off
        if self.__overlay3D not in self.__overlayList:
            
            self.disableListener('showOverlay', self.__name)
            self.showOverlay = False
            self.__showOverlayChanged()
            self.enableListener('showOverlay', self.__name)

        
    def __autoBin(self, data, dataRange):
        """Calculates the number of bins which should be used for a histogram
        of the given data. The calculation is identical to that implemented
        in the original FSLView.

        :arg data:      The data that the histogram is to be calculated on.

        :arg dataRange: A tuple containing the ``(min, max)`` histogram range.
        """

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
            

    def getData(self):
        """Overrides :meth:`.DataSeries.getData`.

        Returns  a tuple containing the ``(x, y)`` histogram data.
        """

        if len(self.__xdata) == 0 or \
           len(self.__ydata) == 0:
            return self.__xdata, self.__ydata

        # If smoothing is not enabled, we'll
        # munge the histogram data a bit so
        # that plt.plot(drawstyle='steps-pre')
        # plots it nicely.
        if not self.__hsPanel.smooth:

            xdata = np.zeros(len(self.__xdata) + 1, dtype=np.float32)
            ydata = np.zeros(len(self.__ydata) + 2, dtype=np.float32)

            xdata[ :-1] = self.__xdata
            xdata[  -1] = self.__xdata[-1]
            ydata[1:-1] = self.__ydata


        # If smoothing is enabled, the above munge
        # is not necessary, and will probably cause
        # the spline interpolation (performed by 
        # the PlotPanel) to fail.
        else:
            xdata = np.array(self.__xdata[:-1], dtype=np.float32)
            ydata = np.array(self.__ydata,      dtype=np.float32)

        nvals    = self.__nvals
        histType = self.__hsPanel.histType
            
        if   histType == 'count':       return xdata, ydata
        elif histType == 'probability': return xdata, ydata / nvals
