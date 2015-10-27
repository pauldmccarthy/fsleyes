#!/usr/bin/env python
#
# histogramseries.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy as np

import props

import fsl.data.image as fslimage
import                   dataseries


log = logging.getLogger(__name__)


class HistogramSeries(dataseries.DataSeries):
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

        dataseries.DataSeries.__init__(self, overlay)

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
