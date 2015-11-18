#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide a view of an image collection.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``views`` package is the home of all *FSLeyes views*, as described in
the :mod:`~fsl.fsleyes` package documentation.  It contains a collection of
:class:`FSLEyesPanel` sub-classes which provide a view of the overlays in an
:class:`.OverlayList`.  The :class:`.ViewPanel` is the base-class for all
views.


The following :class:`.ViewPanel` sub-classes currently exist:

.. autosummary::
   :nosignatures:

   ~fsl.fsleyes.views.canvaspanel.CanvasPanel
   ~fsl.fsleyes.views.orthopanel.OrthoPanel
   ~fsl.fsleyes.views.lightboxpanel.LightBoxPanel
   ~fsl.fsleyes.views.plotpanel.PlotPanel
   ~fsl.fsleyes.views.plotpanel.OverlayPlotPanel
   ~fsl.fsleyes.views.timeseriespanel.TimeSeriesPanel
   ~fsl.fsleyes.views.powerspectrumpanel.PowerSpectrumPanel
   ~fsl.fsleyes.views.histogrampanel.HistogramPanel
"""


import fsl.fsleyes.panel as fslpanel

import viewpanel
import plotpanel
import canvaspanel
import orthopanel
import lightboxpanel
import timeseriespanel
import powerspectrumpanel
import histogrampanel


FSLEyesPanel       = fslpanel          .FSLEyesPanel
ViewPanel          = viewpanel         .ViewPanel
PlotPanel          = plotpanel         .PlotPanel
CanvasPanel        = canvaspanel       .CanvasPanel
OrthoPanel         = orthopanel        .OrthoPanel
LightBoxPanel      = lightboxpanel     .LightBoxPanel
TimeSeriesPanel    = timeseriespanel   .TimeSeriesPanel
PowerSpectrumPanel = powerspectrumpanel.PowerSpectrumPanel
HistogramPanel     = histogrampanel    .HistogramPanel
