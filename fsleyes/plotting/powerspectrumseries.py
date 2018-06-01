#!/usr/bin/env python
#
# powerspectrumseries.py - Classes used by the PowerSpectrumPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides :class:`.DataSeries` sub-classes which are used
by the :class:`.PowerSpectrumPanel` for plotting power spectra.

The following classes are provided:

.. autosummary::
   :nosignatures:

   PowerSpectrumSeries
   VoxelPowerSpectrumSeries
   MelodicPowerSpectrumSeries
"""


import logging

import numpy     as np
import numpy.fft as fft

import fsl.utils.idle        as idle
import fsl.utils.cache       as cache
import fsl.data.melodicimage as fslmelimage
import fsleyes_props         as props
from . import                   dataseries


log = logging.getLogger(__name__)


class PowerSpectrumSeries(dataseries.DataSeries):
    """The ``PowerSpectrumSeries`` encapsulates a power spectrum data series
    from an overlay. The ``PowerSpectrumSeries`` class is the base class for
    all other classes in this module. It provides the :meth:`calcPowerSpectrum`
    method which (surprisingly) calculates the power spectrum of a data
    series.
    """


    varNorm  = props.Boolean(default=True)
    """If ``True``, the data is normalised to unit variance before the fourier
    transformation.
    """


    def __init__(self, overlay, overlayList, displayCtx, plotPanel):
        """Create a ``PowerSpectrumSeries``.

        :arg overlay:     The overlay from which the data to be plotted is
                          retrieved.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg plotPanel:   The :class:`.PlotPanel` that owns this
                          ``PowerSpectrumSeries``.
        """
        dataseries.DataSeries.__init__(
            self, overlay, overlayList, displayCtx, plotPanel)


    def destroy(self):
        """Must be called when this ``PowerSpectrumSeries`` is no longer
        needed.
        """
        dataseries.DataSeries.destroy(self)


    def makeLabel(self):
        """Returns a label that can be used for this ``PowerSpectrumSeries``.
        """
        display = self.displayCtx.getDisplay(self.overlay)
        return display.name


    def calcPowerSpectrum(self, data):
        """Calculates a power spectrum for the given one-dimensional data
        array. If the :attr:`varNorm` property is ``True``, the data is
        de-meaned and normalised by its standard deviation before the fourier
        transformation.
        """
        if self.varNorm:
            mean = data.mean()
            std  = data.std()

            if not np.isclose(std, 0):
                data = data - mean
                data = data / std
            else:
                data = np.zeros(data.shape)

        data = fft.rfft(data)[1:]
        data = np.power(data.real, 2) + np.power(data.imag, 2)

        return data


class VoxelPowerSpectrumSeries(PowerSpectrumSeries):
    """The ``VoxelPowerSpectrumSeries`` class encapsulates the power spectrum
    of a single voxel from a 4D :class:`.Image` overlay. The voxel is dictated
    by the :attr:`.DisplayContext.location` property.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``VoxelPowerSpectrumSeries``.  All arguments are passed
        to the :meth:`PowerSpectrumSeries.__init__` method. A :exc:`ValueError`
        is raised if the overlay is not a 4D :class:`.Image`.
        """

        PowerSpectrumSeries.__init__(self, *args, **kwargs)

        # We use a cache just like in the
        # VoxelTimeSeries class - see that
        # class.
        #
        # TODO You need to invalidate the cache
        #      when the image data changes.
        self.__cache = cache.Cache(maxsize=1000)

        if self.overlay.ndim < 4:
            raise ValueError('Overlay is not a 4D image')


    def makeLabel(self):
        """Creates and returns a label for use with this
        ``VoxelPowerSpectrumSeries``.
        """

        display = self.displayCtx.getDisplay(self.overlay)
        opts    = display.opts
        coords  = opts.getVoxel()

        if coords is not None:
            return '{} [{} {} {}]'.format(display.name,
                                          coords[0],
                                          coords[1],
                                          coords[2])
        else:
            return '{} [out of bounds]'.format(display.name)


    # See VoxelTimeSeries.getData for an
    # explanation of the mutex decorator.
    @idle.mutex
    def getData(self):
        """Returns the data for the current voxel of the overlay. The current
        voxel is dictated by the :attr:`.DisplayContext.location` property.
        """

        opts  = self.displayCtx.getOpts(self.overlay)
        vdim  = opts.volumeDim
        voxel = opts.getVoxel()

        if voxel is None:
            return [], []

        x, y, z = voxel

        ydata = self.__cache.get((x, y, z, vdim), None)

        if ydata is None:
            ydata = self.overlay[opts.index(voxel, atVolume=False)]
            self.__cache.put((x, y, z, vdim), ydata)

        ydata = self.calcPowerSpectrum(ydata)
        xdata = np.arange(len(ydata), dtype=np.float32)

        return xdata, ydata


class MelodicPowerSpectrumSeries(PowerSpectrumSeries):
    """The ``MelodicPowerSpectrumSeries`` class encapsulates the power spectrum
    of the time course for a single component of a :class:`.MelodicImage`. The
    component is dictated by the :attr:`.NiftiOpts.volume` property.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``MelodicPowerSpectrumSeries``. All arguments are passed
        through to the :meth:`PowerSpectrumSeries.__init__` method.
        """
        PowerSpectrumSeries.__init__(self, *args, **kwargs)

        if not isinstance(self.overlay, fslmelimage.MelodicImage):
            raise ValueError('Overlay is not a MelodicImage')

        self.varNorm = False
        self.disableProperty('varNorm')


    def makeLabel(self):
        """Returns a label that can be used for this
        ``MelodicPowerSpectrumSeries``.
        """
        display   = self.displayCtx.getDisplay(self.overlay)
        opts      = display.opts
        component = opts.volume

        return '{} [component {}]'.format(display.name, component + 1)


    def getData(self):
        """Returns the power spectrum for the current component of the
        :class:`.MelodicImage`, as defined by the :attr:`.NiftiOpts.volume`
        property.
        """

        opts      = self.displayCtx.getOpts(self.overlay)
        component = opts.volume

        ydata = self.overlay.getComponentPowerSpectrum(component)
        xdata = np.arange(len(ydata), dtype=np.float32)

        return xdata, ydata



class MeshPowerSpectrumSeries(PowerSpectrumSeries):
    """A ``MeshPowerSpectrumSeries`` object encapsulates the power spectrum for
    the data from a :class:`.Mesh` overlay which has some time series
    vertex data associated with it. See the :attr:`.MeshOpts.vertexData`
    property.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``MeshPowerSpectrumSeries`` instance. All arguments are
        passed through to  :meth:`PowerSpectrumSeries.__init__`.
        """
        PowerSpectrumSeries.__init__(self, *args, **kwargs)


    def makeLabel(self):
        """Returns a label to use for this ``MeshPowerSpectrumSeries`` on the
        legend.
        """

        if self.__haveData():
            display = self.displayCtx.getDisplay(self.overlay)
            opts    = display.opts
            vidx    = opts.getVertex()

            return '{} [{}]'.format(display.name, vidx)

        else:
            return PowerSpectrumSeries.makeLabel(self)


    def __haveData(self):
        """Returns ``True`` if there is currently time series data to show
        for this ``MeshPowerSpectrumSeries``, ``False`` otherwise.
        """
        opts = self.displayCtx.getOpts(self.overlay)
        vidx = opts.getVertex()
        vd   = opts.getVertexData()

        return vidx is not None and vd is not None and vd.shape[1] > 1


    def getData(self):
        """Returns the power spectrum of the data at the current location for
        the :class:`.Mesh`, or ``[], []`` if there is no data.
        """

        if not self.__haveData():
            return [], []

        opts  = self.displayCtx.getOpts(self.overlay)
        vidx  = opts.getVertex()
        vd    = opts.getVertexData()
        ydata = self.calcPowerSpectrum(vd[vidx, :])
        xdata = np.arange(len(ydata))

        return xdata, ydata
