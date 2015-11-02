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
   :nosignature:

   PowerSpectrumSeries
   VoxelPowerSpectrumSeries
   MelodicPowerSpectrumSeries
"""


import logging

import numpy     as np
import numpy.fft as fft

import props

import dataseries


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


    def __init__(self, overlay, displayCtx):
        """Create a ``PowerSpectrumSeries``.

        :arg overlay:    The overlay.
        :arg displayCtx: The :class:`.DisplayContext` instance.
        """
        dataseries.DataSeries.__init__(self, overlay)
        self.displayCtx = displayCtx

        
    def destroy(self):
        """Must be called when this ``PowerSpectrumSeries`` is no longer
        needed.
        """
        self.displayCtx = None
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
            data = data - data.mean()
            data = data / data.std()
        
        data = fft.rfft(data)[1:]
        data = np.power(data.real, 2) + np.power(data.imag, 2)

        return data


class VoxelPowerSpectrumSeries(PowerSpectrumSeries):
    """The ``VoxelPowerSpectrumSeries`` class encapsulates the power spectrum
    of a single voxel from a 4D :class:`.Image` overlay. The voxel is dictated
    by the :attr:`.DisplayContext.location` property.
    """

    
    def makeLabel(self):
        """Creates and returns a label for use with this
        ``VoxelPowerSpectrumSeries``.
        """
        
        display = self.displayCtx.getDisplay(self.overlay)
        opts    = display.getDisplayOpts()
        coords  = opts.getVoxel()

        if coords is not None:
            return '{} [{} {} {}]'.format(display.name,
                                          coords[0],
                                          coords[1],
                                          coords[2])
        else:
            return '{} [out of bounds]'.format(display.name) 


    def getData(self):
        """Returns the data for the current voxel of the overlay. The current
        voxel is dictated by the :attr:`.DisplayContext.location` property.
        """
        
        opts  = self.displayCtx.getOpts(self.overlay)
        voxel = opts.getVoxel()

        if voxel is None:
            return [], []

        x, y, z = voxel

        ydata = self.overlay.data[x, y, z, :]
        ydata = self.calcPowerSpectrum(ydata)
        xdata = np.arange(len(ydata), dtype=np.float32)

        return xdata, ydata


class MelodicPowerSpectrumSeries(PowerSpectrumSeries):
    """The ``MelodicPowerSpectrumSeries`` class encapsulates the power spectrum
    of the time course for a single component of a :class:`.MelodicImage`. The
    component is dictated by the :attr:`.ImageOpts.volume` property.
    """

    
    def __init__(self, *args, **kwargs):
        """Create a ``MelodicPowerSpectrumSeries``. All arguments are passed
        through to the :meth:`PowerSpectrumSeries.__init__` method.
        """
        PowerSpectrumSeries.__init__(self, *args, **kwargs)
        self.varNorm = False
        self.disableProperty('varNorm')

    
    def makeLabel(self):
        """Returns a label that can be used for this
        ``MelodicPowerSpectrumSeries``.
        """
        display   = self.displayCtx.getDisplay(self.overlay)
        opts      = display.getDisplayOpts()
        component = opts.volume

        return '{} [component {}]'.format(display.name, component) 


    def getData(self):
        """Returns the power spectrum for the current component of the
        :class:`.MelodicImage`, as defined by the :attr:`.ImageOpts.volume`
        property.
        """

        opts      = self.displayCtx.getOpts(self.overlay)
        component = opts.volume

        ydata = self.overlay.getComponentPowerSpectrum(component)
        xdata = np.arange(len(ydata), dtype=np.float32)

        return xdata, ydata
