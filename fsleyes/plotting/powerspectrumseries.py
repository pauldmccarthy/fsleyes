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

   PowerSpectrumSeriesMixin
   VoxelPowerSpectrumSeries
   ComplexPowerSpectrumSeries
   ImaginaryPowerSpectrumSeries
   MagnitudePowerSpectrumSeries
   PhasePowerSpecturmSeries
   MelodicPowerSpectrumSeries
"""


import logging

import numpy     as np
import numpy.fft as fft

import fsl.data.melodicimage as fslmelimage
import fsleyes_props         as props
import fsleyes.colourmaps    as fslcm
import fsleyes.strings       as strings
from . import                   dataseries


log = logging.getLogger(__name__)


class PowerSpectrumSeriesMixin(object):
    """The ``PowerSpectrumSeries`` encapsulates a power spectrum data series
    from an overlay. The ``PowerSpectrumSeries`` class is the base class for
    all other classes in this module. It provides the :meth:`calcPowerSpectrum`
    method which calculates the power spectrum of a data series.
    """


    varNorm  = props.Boolean(default=True)
    """If ``True``, the data is normalised to unit variance before the fourier
    transformation.
    """


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


class VoxelPowerSpectrumSeries(dataseries.VoxelDataSeries,
                               PowerSpectrumSeriesMixin):
    """The ``VoxelPowerSpectrumSeries`` class encapsulates the power spectrum
    of a single voxel from a 4D :class:`.Image` overlay. The voxel is dictated
    by the :attr:`.DisplayContext.location` property.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``VoxelPowerSpectrumSeries``.  All arguments are passed
        to the :meth:`VoxelDataSeries.__init__` method. A :exc:`ValueError`
        is raised if the overlay is not a 4D :class:`.Image`.
        """

        dataseries.VoxelDataSeries.__init__(self, *args, **kwargs)

        if self.overlay.ndim < 4:
            raise ValueError('Overlay is not a 4D image')


    def getData(self):
        """Returns the data at the current voxel. """
        ydata = self.dataAtCurrentVoxel()
        ydata = self.calcPowerSpectrum(ydata)
        xdata = np.arange(len(ydata))
        return xdata, ydata


class ComplexPowerSpectrumSeries(VoxelPowerSpectrumSeries):
    """This class is the frequency-spectrum equivalent of the
    :class:`.ComplexTimeSeries` class - see it for more details.
    """

    plotReal      = props.Boolean(default=True)
    plotImaginary = props.Boolean(default=False)
    plotMagnitude = props.Boolean(default=False)
    plotPhase     = props.Boolean(default=False)


    def __init__(self, overlay, overlayList, displayCtx, plotPanel):
        """Create a ``ComplexPowerSpectrumSeries``. All arguments are
        passed through to the :class:`VoxelPowerSpectrumSeries` constructor.
        """

        VoxelPowerSpectrumSeries.__init__(
            self, overlay, overlayList, displayCtx, plotPanel)

        self.__imagps = ImaginaryPowerSpectrumSeries(
            overlay, overlayList, displayCtx, plotPanel)
        self.__magps = MagnitudePowerSpectrumSeries(
            overlay, overlayList, displayCtx, plotPanel)
        self.__phaseps = PhasePowerSpectrumSeries(
            overlay, overlayList, displayCtx, plotPanel)

        for ts in (self.__imagps, self.__magps, self.__phaseps):
            ts.colour = fslcm.randomDarkColour()
            ts.bindProps('alpha',     self)
            ts.bindProps('lineWidth', self)
            ts.bindProps('lineStyle', self)


    def getData(self):
        """If :attr:`plotReal` is true, returns the real component
        of the complex data. Otherwise returns ``(None, None)``.
        """
        if not self.plotReal:
            return None, None
        return VoxelPowerSpectrumSeries.getData(self)


    def dataAtCurrentVoxel(self):
        """Returns the real component of the data at the current voxel. """
        return VoxelPowerSpectrumSeries.dataAtCurrentVoxel(self).real


class ImaginaryPowerSpectrumSeries(VoxelPowerSpectrumSeries):
    """An ``ImaginaryPowerSpectrumSeries`` represents the power spectrum of the
    imaginary component of a complex-valued image.
    ``ImaginaryPowerSpectrumSeries`` instances are created by
    :class:`ComplexPowerSpectrumSeries` instances.
    """


    def makeLabel(self):
        """Returns a string representation of this
        ``ImaginaryPowerSpectrumSeries`` instance.
        """
        return '{} ({})'.format(VoxelPowerSpectrumSeries.makeLabel(self),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the imaginary component of the data at the current voxel.
        """
        return VoxelPowerSpectrumSeries.dataAtCurrentVoxel(self).imag


class MagnitudePowerSpectrumSeries(VoxelPowerSpectrumSeries):
    """An ``MagnitudePowerSpectrumSeries`` represents the magnitude of a
    complex-valued image. ``MagnitudePowerSpectrumSeries`` instances are
    created by :class:`ComplexPowerSpectrumSeries` instances.
    """


    def makeLabel(self):
        """Returns a string representation of this
        ``MagnitudePowerSpectrumSeries`` instance.
        """
        return '{} ({})'.format(MagnitudePowerSpectrumSeries.makeLabel(self),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the magnitude of the data at the current voxel. """
        data = VoxelPowerSpectrumSeries.dataAtCurrentVoxel(self)
        real = data.real
        imag = data.imag
        return np.sqrt(real ** 2 + imag ** 2)


class PhasePowerSpectrumSeries(VoxelPowerSpectrumSeries):
    """An ``PhasePowerSpectrumSeries`` represents the phase of a complex-valued
    image. ``PhasePowerSpectrumSeries`` instances are created by
    :class:`ComplexPowerSpectrumSeries` instances.
    """


    def makeLabel(self):
        """Returns a string representation of this ``PhasePowerSpectrumSeries``
        instance.
        """
        return '{} ({})'.format(VoxelPowerSpectrumSeries.makeLabel(self),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the phase of the data at the current voxel. """
        data = VoxelPowerSpectrumSeries.dataAtCurrentVoxel(self)
        real = data.real
        imag = data.imag
        return np.arctan(real / imag)


class MelodicPowerSpectrumSeries(dataseries.DataSeries,
                                 PowerSpectrumSeriesMixin):
    """The ``MelodicPowerSpectrumSeries`` class encapsulates the power spectrum
    of the time course for a single component of a :class:`.MelodicImage`. The
    component is dictated by the :attr:`.NiftiOpts.volume` property.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``MelodicPowerSpectrumSeries``. All arguments are passed
        through to the :meth:`PowerSpectrumSeries.__init__` method.
        """
        dataseries.DataSeries.__init__(self, *args, **kwargs)

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



class MeshPowerSpectrumSeries(dataseries.DataSeries,
                              PowerSpectrumSeriesMixin):
    """A ``MeshPowerSpectrumSeries`` object encapsulates the power spectrum for
    the data from a :class:`.Mesh` overlay which has some time series
    vertex data associated with it. See the :attr:`.MeshOpts.vertexData`
    property.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``MeshPowerSpectrumSeries`` instance. All arguments are
        passed through to  :meth:`.DataSeries.__init__`.
        """
        dataseries.DataSeries.__init__(self, *args, **kwargs)


    def makeLabel(self):
        """Returns a label to use for this ``MeshPowerSpectrumSeries`` on the
        legend.
        """

        display = self.displayCtx.getDisplay(self.overlay)

        if self.__haveData():
            opts = display.opts
            vidx = opts.getVertex()
            return '{} [{}]'.format(display.name, vidx)

        else:
            return display.name


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
