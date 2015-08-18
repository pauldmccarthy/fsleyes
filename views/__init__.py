#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide a view of an image collection.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains a collection of :class:`wx.Panel` subclasses
which provide a view of an image collection (see
:class:`~fsl.data.image.ImageList`).

The :class:`.FSLEyesPanel` class is the superclass for every view panel.

A convenience function, :func:`listViewPanels`, is provided to allow dynamic
lookup of all :class:`.FSLEyesPanel` types.
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
    :class:`.FSLEyesPanel` classes in the :mod:`views` package.
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
