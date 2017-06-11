#!/usr/bin/env python
#
# histogramseries.py - The HistogramSeries class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramSeries` class, used by the
:class:`.HistogramPanel` for plotting histogram data.
"""

import logging

import numpy as np

import fsleyes_widgets.utils.status as status
import fsl.utils.async              as async
import fsleyes_props                as props
from . import                          dataseries


log = logging.getLogger(__name__)


class HistogramSeries(dataseries.DataSeries):
    """A ``HistogramSeries`` generates histogram data from an :class:`.Image`
    overlay.
    """


    nbins = props.Int(minval=10, maxval=500, default=100, clamped=True)
    """Number of bins to use in the histogram. This value is overridden
    by the :attr:`autoBin` setting.
    """


    autoBin = props.Boolean(default=True)
    """If ``True``, the number of bins used for each :class:`HistogramSeries`
    is calculated automatically. Otherwise, :attr:`HistogramSeries.nbins` bins
    are used.
    """


    ignoreZeros = props.Boolean(default=True)
    """If ``True``, zeros are excluded from the calculated histogram. """


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


    showOverlay = props.Boolean(default=False)
    """If ``True``, a mask :class:`.ProxyImage` overlay is added to the
    :class:`.OverlayList`, which highlights the voxels that have been
    included in the histogram. The mask image is managed by the
    :class:`.HistogramProfile` instance, which manages histogram plot
    interaction.
    """


    showOverlayRange = props.Bounds(ndims=1)
    """Data range to display with the :attr:`.showOverlay` mask. """


    def __init__(self, overlay, displayCtx, overlayList):
        """Create a ``HistogramSeries``.

        :arg overlay:     The :class:`.Image` overlay to calculate a histogram
                          for.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg overlayList: The :class:`.OverlayList` instance.
        """

        log.debug('New HistogramSeries instance for {} '.format(overlay.name))

        dataseries.DataSeries.__init__(self, overlay)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList

        opts = displayCtx.getOpts(overlay)
        self.bindProps('volume', opts)

        self.__nvals              = 0
        self.__finiteData         = np.array([])
        self.__xdata              = np.array([])
        self.__ydata              = np.array([])
        self.__nonZeroData        = np.array([])
        self.__clippedFiniteData  = np.array([])
        self.__clippedNonZeroData = np.array([])
        self.__initProperties()

        self.addListener('volume',
                         self.__name,
                         self.__volumeChanged)
        self.addListener('dataRange',
                         self.__name,
                         self.__dataRangeChanged)
        self.addListener('nbins',
                         self.__name,
                         self.__histPropsChanged)
        self.addListener('autoBin',
                         self.__name,
                         self.__histPropsChanged)
        self.addListener('ignoreZeros',
                         self.__name,
                         self.__histPropsChanged)
        self.addListener('includeOutliers',
                         self.__name,
                         self.__histPropsChanged)


    def destroy(self):
        """This needs to be called when this ``HistogramSeries`` instance
        is no longer being used.
        """

        self.removeListener('nbins',           self.__name)
        self.removeListener('ignoreZeros',     self.__name)
        self.removeListener('includeOutliers', self.__name)
        self.removeListener('volume',          self.__name)
        self.removeListener('dataRange',       self.__name)
        self.removeListener('nbins',           self.__name)


    def redrawProperties(self):
        """Overrides :meth:`.DataSeries.redrawProperties`. The
        ``HistogramSeries`` data does not need to be re-plotted when the
        :attr:`showOverlay` or :attr:`showOverlayRange` properties change.
        """

        propNames = dataseries.DataSeries.redrawProperties(self)

        propNames.remove('showOverlay')
        propNames.remove('showOverlayRange')

        return propNames


    def getData(self):
        """Overrides :meth:`.DataSeries.getData`.

        Returns  a tuple containing the ``(x, y)`` histogram data.
        """

        return self.__xdata, self.__ydata


    def getVertexData(self):
        """Returns a ``numpy`` array of shape ``(N, 2)``, which contains a
        set of "vertices" which can be used to display the histogram data
        as a filled polygon.
        """

        x, y  = self.getData()
        verts = np.zeros((len(x) * 2, 2), dtype=x.dtype)

        verts[  :,   0] = x.repeat(2)
        verts[ 1:-1, 1] = y.repeat(2)

        return verts


    def getNumHistogramValues(self):
        """Returns the number of values which were used in calculating the
        histogram.
        """
        return self.__nvals


    def __initProperties(self):
        """Called by :meth:`__init__`. Calculates and caches some things which
        are needed for the histogram calculation.

        .. note:: The work performed by this method is done on a separate
                  thread, via the :mod:`.async` module. If you want to be
                  notified when the work is complete, register a listener on
                  the :attr:`dataRange` property (via
                  :meth:`.HasProperties.addListener`).
        """

        log.debug('Performining initial histogram '
                  'calculations for overlay {}'.format(
                      self.overlay.name))

        status.update('Performing initial histogram calculation '
                      'for overlay {}...'.format(self.overlay.name))

        def init():

            data    = self.overlay[:]
            finData = data[np.isfinite(data)]
            nzData  = finData[finData != 0]

            dmin    = finData.min()
            dmax    = finData.max()
            dist    = (dmax - dmin) / 10000.0

            with props.suppress(self, 'showOverlayRange'), \
                 props.suppress(self, 'dataRange'), \
                 props.suppress(self, 'nbins'):

                self.dataRange.xmin = dmin
                self.dataRange.xmax = dmax + dist
                self.dataRange.xlo  = dmin
                self.dataRange.xhi  = dmax + dist

                self.nbins = self.__autoBin(nzData, self.dataRange.x)

            if not self.overlay.is4DImage():

                self.__finiteData  = finData
                self.__nonZeroData = nzData
                self.__dataRangeChanged(callHistPropsChanged=False)

            else:
                self.__volumeChanged(callHistPropsChanged=False)

            self.__histPropsChanged()

        def onFinish():
            self.propNotify('dataRange')

        async.run(init, onFinish=onFinish)


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

        if self.overlay.is4DImage(): data = self.overlay[..., self.volume]
        else:                        data = self.overlay[:]

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


        with props.suppress(self, 'showOverlayRange', notify=True):

            dlo, dhi = self.dataRange.x
            dist     = (dhi - dlo) / 10000.0

            needsInit = np.all(np.isclose(self.showOverlayRange.x, [0, 0]))

            self.showOverlayRange.xmin = dlo - dist
            self.showOverlayRange.xmax = dhi + dist

            if needsInit:
                self.showOverlayRange.xlo = dlo
                self.showOverlayRange.xhi = dhi
            else:
                self.showOverlayRange.xlo = max(dlo, self.showOverlayRange.xlo)
                self.showOverlayRange.xhi = min(dhi, self.showOverlayRange.xhi)

        if callHistPropsChanged:
            self.__histPropsChanged()


    def __histPropsChanged(self, *a):
        """Called internally, and when any histogram settings change.
        Re-calculates the histogram data.
        """

        log.debug('Calculating histogram for '
                  'overlay {}'.format(self.overlay.name))

        status.update('Calculating histogram for '
                      'overlay {}'.format(self.overlay.name))

        if np.isclose(self.dataRange.xhi, self.dataRange.xlo):
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

        if self.autoBin:
            nbins = self.__autoBin(data, self.dataRange.x)

            if self.hasListener('nbins', self.__name):
                self.disableListener('nbins', self.__name)
            self.nbins = nbins
            if self.hasListener('nbins', self.__name):
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

        status.update('Histogram for {} calculated.'.format(
            self.overlay.name))

        log.debug('Calculated histogram for overlay '
                  '{} (number of values: {}, number '
                  'of bins: {})'.format(
                      self.overlay.name,
                      self.__nvals,
                      self.nbins))


    def __autoBin(self, data, dataRange):
        """Calculates the number of bins which should be used for a histogram
        of the given data. The calculation is identical to that implemented
        in the original FSLView.

        :arg data:      The data that the histogram is to be calculated on.

        :arg dataRange: A tuple containing the ``(min, max)`` histogram range.
        """

        dMin, dMax = dataRange
        dRange     = dMax - dMin

        if np.isclose(dRange, 0):
            return 1

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
