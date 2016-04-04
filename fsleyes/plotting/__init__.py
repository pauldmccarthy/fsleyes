#!/usr/bin/env python
#
# __init__.py - Classes used by PlotPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``plotting`` package contains the :class:`.DataSeries` class, and
all of its sub-classes. These classes are used by :class:`.PlotPanel` views
for plotting data, and are defined in the following sub-modules:

.. autosummary::

   ~fsl.fsleyes.plotting.dataseries
   ~fsl.fsleyes.plotting.timeseries
   ~fsl.fsleyes.plotting.histogramseries
   ~fsl.fsleyes.plotting.powerspectrumseries
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
