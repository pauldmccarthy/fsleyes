#!/usr/bin/env python
#
# __init__.py - Classes used by PlotPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``plotting`` package contains the :class:`.DataSeries` class, and
all of its sub-classes. These classes are used by :class:`.PlotPanel` views
for plotting data.
"""


from . import dataseries
from . import timeseries
from . import histogramseries
from . import powerspectrumseries

DataSeries                   = dataseries         .DataSeries
VoxelDataSeries              = dataseries         .VoxelDataSeries
VoxelTimeSeries              = timeseries         .VoxelTimeSeries
ComplexTimeSeries            = timeseries         .ComplexTimeSeries
ImaginaryTimeSeries          = timeseries         .ImaginaryTimeSeries
MagnitudeTimeSeries          = timeseries         .MagnitudeTimeSeries
PhaseTimeSeries              = timeseries         .PhaseTimeSeries
FEATTimeSeries               = timeseries         .FEATTimeSeries
FEATPartialFitTimeSeries     = timeseries         .FEATPartialFitTimeSeries
FEATEVTimeSeries             = timeseries         .FEATEVTimeSeries
FEATResidualTimeSeries       = timeseries         .FEATResidualTimeSeries
FEATModelFitTimeSeries       = timeseries         .FEATModelFitTimeSeries
MelodicTimeSeries            = timeseries         .MelodicTimeSeries
MeshTimeSeries               = timeseries         .MeshTimeSeries
HistogramSeries              = histogramseries    .HistogramSeries
ImageHistogramSeries         = histogramseries    .ImageHistogramSeries
MeshHistogramSeries          = histogramseries    .MeshHistogramSeries
PowerSpectrumSeries          = powerspectrumseries.PowerSpectrumSeries
VoxelPowerSpectrumSeries     = powerspectrumseries.VoxelPowerSpectrumSeries
ComplexPowerSpectrumSeries   = powerspectrumseries.ComplexPowerSpectrumSeries
ImaginaryPowerSpectrumSeries = powerspectrumseries.ImaginaryPowerSpectrumSeries
MagnitudePowerSpectrumSeries = powerspectrumseries.MagnitudePowerSpectrumSeries
PhasePowerSpectrumSeries     = powerspectrumseries.PhasePowerSpectrumSeries
MelodicPowerSpectrumSeries   = powerspectrumseries.MelodicPowerSpectrumSeries
MeshPowerSpectrumSeries      = powerspectrumseries.MeshPowerSpectrumSeries
