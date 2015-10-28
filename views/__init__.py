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


A package-level convenience function, :func:`listViewPanels`, is provided to
allow dynamic lookup of all :class:`.ViewPanel` sub-classes. The following
:class:`.ViewPanel` sub-classes currently exist:

.. autosummary::
   :nosignatures:

   ~fsl.fsleyes.views.canvaspanel.CanvasPanel
   ~fsl.fsleyes.views.orthopanel.OrthoPanel
   ~fsl.fsleyes.views.lightboxpanel.LightBoxPanel
   ~fsl.fsleyes.views.plotpanel.PlotPanel
   ~fsl.fsleyes.views.timeseriespanel.TimeSeriesPanel
   ~fsl.fsleyes.views.histogrampanel.HistogramPanel
"""


import fsl.fsleyes.panel as fslpanel

import viewpanel
import plotpanel
import canvaspanel
import orthopanel
import lightboxpanel
import timeseriespanel
import histogrampanel


FSLEyesPanel    = fslpanel       .FSLEyesPanel
ViewPanel       = viewpanel      .ViewPanel
PlotPanel       = plotpanel      .PlotPanel
CanvasPanel     = canvaspanel    .CanvasPanel
OrthoPanel      = orthopanel     .OrthoPanel
LightBoxPanel   = lightboxpanel  .LightBoxPanel
TimeSeriesPanel = timeseriespanel.TimeSeriesPanel
HistogramPanel  = histogrampanel .HistogramPanel


def listViewPanels():
    """Convenience function which returns a list containing all
    :class:`.ViewPanel` sub-classes in the ``views`` package.
    """

    atts = globals()

    viewPanels = []

    for name, val in atts.items():
        
        if not isinstance(val, type): continue
        if val == FSLEyesPanel:       continue
            
        if issubclass(val, FSLEyesPanel) and \
           val not in (CanvasPanel, ViewPanel, PlotPanel):
            viewPanels.append(val)
            
    return viewPanels
