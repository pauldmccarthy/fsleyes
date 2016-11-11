#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide a view of an image collection.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``views`` package is the home of all *FSLeyes views*, as described in
the :mod:`~fsleyes` package documentation.  It contains a collection of
:class:`FSLeyesPanel` sub-classes which provide a view of the overlays in an
:class:`.OverlayList`.  The :class:`.ViewPanel` is the base-class for all
views.
"""


import fsleyes.panel as fslpanel

from . import viewpanel
from . import plotpanel
from . import canvaspanel
from . import orthopanel
from . import lightboxpanel
from . import timeseriespanel
from . import powerspectrumpanel
from . import histogrampanel
from . import shellpanel


FSLeyesPanel       = fslpanel          .FSLeyesPanel
ViewPanel          = viewpanel         .ViewPanel
PlotPanel          = plotpanel         .PlotPanel
OverlayPlotPanel   = plotpanel         .OverlayPlotPanel
CanvasPanel        = canvaspanel       .CanvasPanel
OrthoPanel         = orthopanel        .OrthoPanel
LightBoxPanel      = lightboxpanel     .LightBoxPanel
TimeSeriesPanel    = timeseriespanel   .TimeSeriesPanel
PowerSpectrumPanel = powerspectrumpanel.PowerSpectrumPanel
HistogramPanel     = histogrampanel    .HistogramPanel
ShellPanel         = shellpanel        .ShellPanel
