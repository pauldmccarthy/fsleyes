#!/usr/bin/env python
#
# histogramseries.py - The HistogramSeries class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramSeries`,
 :class:`ImageHistogramSeries`, :class:`ComplexHistogramSeries`, and
 :class:`MeshHistogramSeries` classes, used by the :class:`.HistogramPanel`
 for plotting histogram data.

Two standalone functions are also defined in this module:

  .. autosummary::
     :nosignatures:

     histogram
     autoBin
"""

import logging

import numpy as np

import fsl.utils.cache              as cache
import fsleyes_widgets.utils.status as status
import fsleyes_props                as props
import fsleyes.colourmaps           as fslcm
from . import                          dataseries


log = logging.getLogger(__name__)


class HistogramSeries(dataseries.DataSeries):
    """A ``HistogramSeries`` generates histogram data from an overlay. It is
    the base class for the :class:`ImageHistogramSeriess` and
    :class:`MeshHistogramSeries` classes.
    """


    nbins = props.Int(minval=10, maxval=1000, default=100, clamped=False)
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


    dataRange = props.Bounds(ndims=1, clamped=False)
    """Specifies the range of data which should be included in the histogram.
    See the :attr:`includeOutliers` property.
    """


    def __init__(self, overlay, overlayList, displayCtx, plotCanvas):
        """Create a ``HistogramSeries``.

        :arg overlay:     The overlay from which the data to be plotted is
                          retrieved.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg plotCanvas:   The :class:`.HistogramPanel` that owns this
                          ``HistogramSeries``.
        """

        log.debug('New HistogramSeries instance for {} '.format(overlay.name))

        dataseries.DataSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)

        self.__nvals              = 0
        self.__dataKey            = None
        self.__xdata              = np.array([])
        self.__ydata              = np.array([])
        self.__finiteData         = np.array([])
        self.__nonZeroData        = np.array([])
        self.__clippedFiniteData  = np.array([])
        self.__clippedNonZeroData = np.array([])
        self.__dataCache          = cache.Cache(maxsize=10)
        self.__histCache          = cache.Cache(maxsize=100)

        self.addListener('dataRange',       self.name, self.__dataRangeChanged)
        self.addListener('nbins',           self.name, self.__histPropsChanged)
        self.addListener('autoBin',         self.name, self.__histPropsChanged)
        self.addListener('ignoreZeros',     self.name, self.__histPropsChanged)
        self.addListener('includeOutliers', self.name, self.__histPropsChanged)


    def destroy(self):
        """This needs to be called when this ``HistogramSeries`` instance
        is no longer being used.
        """

        self.removeListener('nbins',           self.name)
        self.removeListener('ignoreZeros',     self.name)
        self.removeListener('includeOutliers', self.name)
        self.removeListener('dataRange',       self.name)
        self.removeListener('nbins',           self.name)

        self.__dataCache.clear()
        self.__histCache.clear()
        self.__dataCache          = None
        self.__histCache          = None
        self.__nvals              = 0
        self.__dataKey            = None
        self.__xdata              = None
        self.__ydata              = None
        self.__finiteData         = None
        self.__nonZeroData        = None
        self.__clippedFiniteData  = None
        self.__clippedNonZeroData = None
        dataseries.DataSeries.destroy(self)


    def setHistogramData(self, data, key):
        """Must be called by sub-classes whenever the underlying histogram data
        changes.

        :arg data: A ``numpy`` array containing the data that the histogram is
                   to be calculated on. Pass in ``None``  to indicate that
                   there is currently no histogram data.

        :arg key:  Something which identifies the ``data``, and can be used as
                   a ``dict`` key.
        """

        if data is None:
            self.__nvals              = 0
            self.__dataKey            = None
            self.__xdata              = np.array([])
            self.__ydata              = np.array([])
            self.__finiteData         = np.array([])
            self.__nonZeroData        = np.array([])
            self.__clippedFiniteData  = np.array([])
            self.__clippedNonZeroData = np.array([])

            # force the panel to refresh
            with props.skip(self, 'dataRange', self.name):
                self.propNotify('dataRange')
            return

        # We cache the following data, based
        # on the provided key, so they don't
        # need to be recalculated:
        #  - finite data
        #  - non-zero data
        #  - finite minimum
        #  - finite maximum
        #
        # The cache size is restricted (see its
        # creation in __init__) so we don't blow
        # out RAM
        cached = self.__dataCache.get(key, None)

        if cached is None:

            log.debug('New histogram data {} - extracting '
                      'finite/non-zero data'.format(key))

            finData = data[np.isfinite(data)]
            nzData  = finData[finData != 0]
            dmin    = finData.min()
            dmax    = finData.max()

            self.__dataCache.put(key, (finData, nzData, dmin, dmax))
        else:
            log.debug('Got histogram data {} from cache'.format(key))
            finData, nzData, dmin, dmax = cached

        # The upper bound on the dataRange
        # is exclusive, so we initialise it
        # to a bit more than the data max.
        dist = (dmax - dmin) / 10000.0

        with props.suppressAll(self):

            self.dataRange.xmin = dmin
            self.dataRange.xmax = dmax + dist
            self.dataRange.xlo  = dmin
            self.dataRange.xhi  = dmax + dist
            self.nbins          = autoBin(nzData, self.dataRange.x)

            self.__dataKey     = key
            self.__finiteData  = finData
            self.__nonZeroData = nzData

            self.__dataRangeChanged()

        with props.skip(self, 'dataRange', self.name):
            self.propNotify('dataRange')


    def onDataRangeChange(self):
        """May be implemented by sub-classes. Is called when the
        :attr:`dataRange` changes.
        """
        pass


    def getData(self):
        """Overrides :meth:`.DataSeries.getData`.

        Returns  a tuple containing the ``(x, y)`` histogram data.
        """

        return self.__xdata, self.__ydata


    @property
    def binWidth(self):
        """Returns the width of one bin for this :class:`HistogramSeries`. """
        lo, hi = self.dataRange.x
        return (hi - lo) / self.nbins


    def getVertexData(self):
        """Returns a ``numpy`` array of shape ``(N, 2)``, which contains a
        set of "vertices" which can be used to display the histogram data
        as a filled polygon.
        """

        x, y = self.getData()

        if x is None or y is None:
            return None

        verts = np.zeros((len(x) * 2, 2), dtype=x.dtype)

        verts[  :,   0] = x.repeat(2)
        verts[ 1:-1, 1] = y.repeat(2)

        return verts


    @property
    def numHistogramValues(self):
        """Returns the number of values which were used in calculating the
        histogram.
        """
        return self.__nvals


    def __dataRangeChanged(self, *args, **kwargs):
        """Called when the :attr:`dataRange` property changes, and also by the
        :meth:`__initProperties` and :meth:`__volumeChanged` methods.
        """

        finData = self.__finiteData
        nzData  = self.__nonZeroData

        self.__clippedFiniteData  = finData[(finData >= self.dataRange.xlo) &
                                            (finData <  self.dataRange.xhi)]
        self.__clippedNonZeroData = nzData[ (nzData  >= self.dataRange.xlo) &
                                            (nzData  <  self.dataRange.xhi)]

        self.onDataRangeChange()
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

        # Figure out the number of bins to use
        if self.autoBin: nbins = autoBin(data, self.dataRange.x)
        else:            nbins = self.nbins

        # nbins is unclamped, but
        # we don't allow < 10
        if nbins < 10:
            nbins = 10

        # Update the nbins property
        with props.skip(self, 'nbins', self.name):
            self.nbins = nbins

        # We cache calculated bins and counts
        # for each combination of parameters,
        # as histogram calculation can take
        # time.
        hrange  = (self.dataRange.xlo,  self.dataRange.xhi)
        drange  = (self.dataRange.xmin, self.dataRange.xmax)
        histkey = (self.__dataKey,
                   self.includeOutliers,
                   self.ignoreZeros,
                   hrange,
                   drange,
                   self.nbins)
        cached  = self.__histCache.get(histkey, None)

        if cached is not None:
            histX, histY, nvals = cached
        else:
            histX, histY, nvals = histogram(data,
                                            self.nbins,
                                            hrange,
                                            drange,
                                            self.includeOutliers,
                                            True)
            self.__histCache.put(histkey, (histX, histY, nvals))

        self.__xdata = histX
        self.__ydata = histY
        self.__nvals = nvals

        status.update('Histogram for {} calculated.'.format(
            self.overlay.name))

        log.debug('Calculated histogram for overlay '
                  '{} (number of values: {}, number '
                  'of bins: {})'.format(
                      self.overlay.name,
                      self.__nvals,
                      self.nbins))


class ImageHistogramSeries(HistogramSeries):
    """An ``ImageHistogramSeries`` instance manages generation of histogram
    data for an :class:`.Image` overlay.
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


    def __init__(self, *args, **kwargs):
        """Create an ``ImageHistogramSeries``. All arguments are passed
        through to :meth:`HistogramSeries.__init__`.
        """

        HistogramSeries.__init__(self, *args, **kwargs)

        self.__display = self.displayCtx.getDisplay(self.overlay)
        self.__opts    = self.displayCtx.getOpts(   self.overlay)

        self.__display.addListener('overlayType',
                                   self.name,
                                   self.__overlayTypeChanged)
        self.__opts   .addListener('volume',
                                   self.name,
                                   self.__volumeChanged)
        self.__opts   .addListener('volumeDim',
                                   self.name,
                                   self.__volumeChanged)

        self.__volumeChanged()


    def destroy(self):
        """Must be called when this ``ImageHistogramSeries`` is no longer
        needed. Removes some property listeners, and calls
        :meth:`HistogramSeries.destroy`.
        """

        HistogramSeries.destroy(self)

        self.__display.removeListener('overlayType', self.name)
        self.__opts   .removeListener('volume',      self.name)
        self.__opts   .removeListener('volumeDim',   self.name)


    def redrawProperties(self):
        """Overrides :meth:`.DataSeries.redrawProperties`. The
        ``HistogramSeries`` data does not need to be re-plotted when the
        :attr:`showOverlay` or :attr:`showOverlayRange` properties change.
        """

        propNames = dataseries.DataSeries.redrawProperties(self)

        propNames.remove('showOverlay')
        propNames.remove('showOverlayRange')

        return propNames


    def onDataRangeChange(self):
        """Overrides :meth:`HistogramSeries.onDataRangeChange`. Makes sure
        that the :attr:`showOverlayRange` limits are synced to the
        :attr:`HistogramSeries.dataRange`.
        """
        with props.suppress(self, 'showOverlayRange', notify=True):

            dlo, dhi = self.dataRange.x
            dist     = (dhi - dlo) / 10000.0

            needsInit = np.all(np.isclose(self.showOverlayRange.x, [0, 0]))

            self.showOverlayRange.xmin = dlo - dist
            self.showOverlayRange.xmax = dhi + dist

            if needsInit or not self.showOverlay:
                self.showOverlayRange.xlo = dlo
                self.showOverlayRange.xhi = dhi
            else:
                self.showOverlayRange.xlo = max(dlo, self.showOverlayRange.xlo)
                self.showOverlayRange.xhi = min(dhi, self.showOverlayRange.xhi)


    def __volumeChanged(self, *args, **kwargs):
        """Called when the :attr:`volume` property changes, and also by the
        :meth:`__init__` method.

        Passes the data to the :meth:`HistogramSeries.setHistogramData` method.
        """

        opts    = self.__opts
        overlay = self.overlay
        volkey  = (opts.volumeDim, opts.volume)

        self.setHistogramData(overlay[opts.index()], volkey)


    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` changes. When this
        happens, the :class:`.DisplayOpts` instance associated with the
        overlay gets destroyed and recreated. This method de-registers
        and re-registers property listeners as needed.
        """
        oldOpts     = self.__opts
        newOpts     = self.displayCtx.getOpts(self.overlay)
        self.__opts = newOpts

        oldOpts.removeListener('volume',    self.name)
        oldOpts.removeListener('volumeDim', self.name)
        newOpts.addListener(   'volume',    self.name, self.__volumeChanged)
        newOpts.addListener(   'volumeDim', self.name, self.__volumeChanged)


class ComplexHistogramSeries(ImageHistogramSeries):
    """Thre ``ComplexHistogramSeries`` class is a specialisation of the
    :class:`ImageHistogramSeries` for images with a complex data type.

    See also the :class:`.ComplexTimeSeries` and
    :class:`.ComplexPowerSpectrumSeries` classes.
    """


    plotReal      = props.Boolean(default=True)
    plotImaginary = props.Boolean(default=False)
    plotMagnitude = props.Boolean(default=False)
    plotPhase     = props.Boolean(default=False)


    def __init__(self, *args, **kwargs):
        """Create a ``ComplexHistogramSeries``. All arguments are passed
        through to the ``ImageHistogramSeries`` constructor.
        """
        ImageHistogramSeries.__init__(self, *args, **kwargs)

        self.__imaghs  = ImaginaryHistogramSeries(*args, **kwargs)
        self.__maghs   = MagnitudeHistogramSeries(*args, **kwargs)
        self.__phasehs = PhaseHistogramSeries(    *args, **kwargs)

        for hs in (self.__imaghs, self.__maghs, self.__phasehs):
            hs.colour = fslcm.randomDarkColour()
            hs.bindProps('alpha',           self)
            hs.bindProps('lineWidth',       self)
            hs.bindProps('lineStyle',       self)
            hs.bindProps('autoBin',         self)
            hs.bindProps('ignoreZeros',     self)
            hs.bindProps('includeOutliers', self)


    def extraSeries(self):
        """Returns a list containing an :class:`ImaginaryHistogramSeries`,
        :class:`MagnitudeHistogramSeries`, and/or
        :class:`PhaseHistogramSeries`, depending on the values of the
        :attr:`plotImaginary`, :attr:`plotMagnitude`, and :attr:`plotPhase`
        properties.
        """
        extras = []
        if self.plotImaginary: extras.append(self.__imaghs)
        if self.plotMagnitude: extras.append(self.__maghs)
        if self.plotPhase:     extras.append(self.__phasehs)
        return extras


    def getData(self):
        """Overrides :meth:`HistogramSeries.setHistogramData`. If
        :attr:`plotReal` is ``False``, returns ``(None, None)``. Otherwise
        returns the parent class implementation.
        """
        if self.plotReal: return ImageHistogramSeries.getData(self)
        else:             return None, None


    def setHistogramData(self, data, key):
        """Overrides :meth:`HistogramSeries.setHistogramData`.  The real
        component of the data is passed to the parent class implementation.
        """
        data = data.real
        ImageHistogramSeries.setHistogramData(self, data, key)


class ImaginaryHistogramSeries(ImageHistogramSeries):
    """Class which plots the histogram of the imaginary component
    of a complex-valued image.
    """
    def setHistogramData(self, data, key):
        data = data.imag
        ImageHistogramSeries.setHistogramData(self, data, key)


class MagnitudeHistogramSeries(ImageHistogramSeries):
    """Class which plots the histogram of the magnitude of a complex-valued
    image.
    """
    def setHistogramData(self, data, key):
        data = (data.real ** 2 + data.imag ** 2) ** 0.5
        ImageHistogramSeries.setHistogramData(self, data, key)


class PhaseHistogramSeries(ImageHistogramSeries):
    """Class which plots the histogram of the phase of a complex-valued image.
    """
    def setHistogramData(self, data, key):
        data = np.arctan2(data.imag, data.real)
        ImageHistogramSeries.setHistogramData(self, data, key)


class MeshHistogramSeries(HistogramSeries):
    """A ``MeshHistogramSeries`` instance manages generation of histogram
    data for a :class:`.Mesh` overlay.
    """

    def __init__(self, *args, **kwargs):
        """Create a ``MeshHistogramSeries``. All arguments are passed
        through to :meth:`HistogramSeries.__init__`.
        """

        HistogramSeries.__init__(self, *args, **kwargs)

        self.__opts = self.displayCtx.getOpts(self.overlay)

        self.__opts.addListener('vertexData',
                                self.name,
                                self.__vertexDataChanged)
        self.__opts.addListener('vertexDataIndex',
                                self.name,
                                self.__vertexDataChanged)

        self.__vertexDataChanged()


    def destroy(self):
        """Must be called when this ``MeshHistogramSeries`` is no longer
        needed. Calls :meth:`HistogramSeries.destroy` and removes some
        property listeners.
        """
        HistogramSeries.destroy(self)
        self.__opts.removeListener('vertexData',      self.name)
        self.__opts.removeListener('vertexDataIndex', self.name)
        self.__opts = None


    def __vertexDataChanged(self, *a):
        """Called when the :attr:`.MeshOpts.vertexData` or
        :attr:`.MeshOpts.vertexDataIndex` properties change. Updates the
        histogram data via :meth:`HistogramSeries.setHistogramData`.
        """

        vdname = self.__opts.vertexData
        vdi    = self.__opts.vertexDataIndex
        vd     = self.__opts.getVertexData()

        if vd is None: self.setHistogramData(None, None)
        else:          self.setHistogramData(vd[:, vdi],   (vdname, vdi))


def histogram(data,
              nbins,
              histRange,
              dataRange,
              includeOutliers=False,
              count=True):
    """Calculates a histogram of the given ``data``.

    :arg data:            The data to calculate a histogram foe

    :arg nbins:           Number of bins to use

    :arg histRange:       Tuple containing  the ``(low, high)`` data range
                          that the histogram is to be calculated on.

    :arg dataRange:       Tuple containing  the ``(min, max)`` range of
                          values in the data

    :arg includeOutliers: If ``True``, the outermost bins will contain counts
                          for values which are outside the ``histRange``.
                          Defaults to ``False``.

    :arg count:           If ``True`` (the default), the raw histogram counts
                          are returned. Otherwise they are converted into
                          probabilities.

    :returns:             A tuple containing:

                           - The ``x`` histogram data (bin edges)

                           - The ``y`` histogram data

                           - The total number of values that were used
                             in the histogram calculation
    """

    hlo, hhi = histRange
    dlo, dhi = dataRange

    # Calculate bin edges
    bins = np.linspace(hlo, hhi, nbins + 1)

    if includeOutliers:
        bins[ 0] = dlo
        bins[-1] = dhi

    # Calculate the histogram
    histX    = bins
    histY, _ = np.histogram(data.flat, bins=bins)
    nvals    = histY.sum()

    if not count:
        histY = histY / nvals

    return histX, histY, nvals


def autoBin(data, dataRange):
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
