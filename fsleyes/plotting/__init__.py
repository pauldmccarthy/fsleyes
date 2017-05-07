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

DataSeries                 = dataseries         .DataSeries
TimeSeries                 = timeseries         .TimeSeries
VoxelTimeSeries            = timeseries         .VoxelTimeSeries
FEATTimeSeries             = timeseries         .FEATTimeSeries
FEATPartialFitTimeSeries   = timeseries         .FEATPartialFitTimeSeries
FEATEVTimeSeries           = timeseries         .FEATEVTimeSeries
FEATResidualTimeSeries     = timeseries         .FEATResidualTimeSeries
FEATModelFitTimeSeries     = timeseries         .FEATModelFitTimeSeries
MelodicTimeSeries          = timeseries         .MelodicTimeSeries
HistogramSeries            = histogramseries    .HistogramSeries
PowerSpectrumSeries        = powerspectrumseries.PowerSpectrumSeries
VoxelPowerSpectrumSeries   = powerspectrumseries.VoxelPowerSpectrumSeries
MelodicPowerSpectrumSeries = powerspectrumseries.MelodicPowerSpectrumSeries
