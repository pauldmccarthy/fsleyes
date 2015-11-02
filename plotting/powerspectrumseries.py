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
    """
    """

    
    varNorm  = props.Boolean(default=True)
    """Normalise data to unit variance before fourier transformation. """


    def __init__(self, overlay, displayCtx):
        """
        """
        dataseries.DataSeries.__init__(self, overlay)
        self.displayCtx = displayCtx

        
    def destroy(self):
        """
        """
        self.displayCtx = None
        dataseries.DataSeries.destroy(self)


    def makeLabel(self):
        """
        """
        display = self.displayCtx.getDisplay(self.overlay)
        return display.name


    def calcPowerSpectrum(self, data):
        if self.varNorm:
            data = data - data.mean()
            data = data / data.std()
        
        data = fft.rfft(data)[1:]
        data = np.power(data.real, 2) + np.power(data.imag, 2)

        return data


class VoxelPowerSpectrumSeries(PowerSpectrumSeries):

    def makeLabel(self):
        """
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
        """
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
    """
    """

    
    def __init__(self, *args, **kwargs):
        """
        """
        PowerSpectrumSeries.__init__(self, *args, **kwargs)
        self.varNorm = False
        self.disableProperty('varNorm')

    
    def makeLabel(self):
        """
        """
        display   = self.displayCtx.getDisplay(self.overlay)
        opts      = display.getDisplayOpts()
        component = opts.volume

        return '{} [component {}]'.format(display.name, component) 


    def getData(self):
        """
        """

        opts      = self.displayCtx.getOpts(self.overlay)
        component = opts.volume

        ydata = self.overlay.getComponentPowerSpectrum(component)
        xdata = np.arange(len(ydata), dtype=np.float32)

        return xdata, ydata
