#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide a view of an image collection.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``views`` package is the home of all *FSLeyes views*, as described in
the :mod:`~fsleyes` package documentation.  It contains a collection of
:class:`FSLEyesPanel` sub-classes which provide a view of the overlays in an
:class:`.OverlayList`.  The :class:`.ViewPanel` is the base-class for all
views.


The following :class:`.ViewPanel` sub-classes currently exist:

.. autosummary::
   :nosignatures:

   ~fsleyes.views.canvaspanel.CanvasPanel
   ~fsleyes.views.orthopanel.OrthoPanel
   ~fsleyes.views.lightboxpanel.LightBoxPanel
   ~fsleyes.views.plotpanel.PlotPanel
   ~fsleyes.views.plotpanel.OverlayPlotPanel
   ~fsleyes.views.timeseriespanel.TimeSeriesPanel
   ~fsleyes.views.powerspectrumpanel.PowerSpectrumPanel
   ~fsleyes.views.histogrampanel.HistogramPanel
   ~fsleyes.views.shellpanel.ShellPanel
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


FSLEyesPanel       = fslpanel          .FSLEyesPanel
ViewPanel          = viewpanel         .ViewPanel
PlotPanel          = plotpanel         .PlotPanel
CanvasPanel        = canvaspanel       .CanvasPanel
OrthoPanel         = orthopanel        .OrthoPanel
LightBoxPanel      = lightboxpanel     .LightBoxPanel
TimeSeriesPanel    = timeseriespanel   .TimeSeriesPanel
PowerSpectrumPanel = powerspectrumpanel.PowerSpectrumPanel
HistogramPanel     = histogrampanel    .HistogramPanel
ShellPanel         = shellpanel        .ShellPanel
