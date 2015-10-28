#!/usr/bin/env python
#
# __init__.py - FSLeyes control panels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``controls`` package is the home of all *FSLeyes controls*, as
described in the :mod:`~fsl.fsleyes` package documentation.


Every control panel is a sub-class of either the :class:`.FSLEyesPanel` or
:class:`.FSLEyesToolBar`, and each panel allows the user to control some
aspect of either the specific :class:`.ViewPanel` that the control panel is
embedded within, or some general aspect of *FSLeyes*.


The following control panels currently exist:

.. autosummary::
   :nosignatures:

   ~fsl.fsleyes.controls.atlaspanel.AtlasPanel
   ~fsl.fsleyes.controls.canvassettingspanel.CanvasSettingsPanel
   ~fsl.fsleyes.controls.clusterpanel.ClusterPanel
   ~fsl.fsleyes.controls.histogramcontrolpanel.HistogramControlPanel
   ~fsl.fsleyes.controls.histogramlistpanel.HistogramListPanel
   ~fsl.fsleyes.controls.lightboxtoolbar.LightBoxToolBar
   ~fsl.fsleyes.controls.locationpanel.LocationPanel
   ~fsl.fsleyes.controls.lookuptablepanel.LookupTablePanel
   ~fsl.fsleyes.controls.orthoedittoolbar.OrthoEditToolBar
   ~fsl.fsleyes.controls.orthotoolbar.OrthoToolBar
   ~fsl.fsleyes.controls.overlaydisplaypanel.OverlayDisplayPanel
   ~fsl.fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar
   ~fsl.fsleyes.controls.overlayinfopanel.OverlayInfoPanel
   ~fsl.fsleyes.controls.overlaylistpanel.OverlayListPanel
   ~fsl.fsleyes.controls.shellpanel.ShellPanel
   ~fsl.fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel
   ~fsl.fsleyes.controls.timeserieslistpanel.TimeSeriesListPanel
"""
