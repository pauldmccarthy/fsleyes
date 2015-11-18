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
   ~fsl.fsleyes.controls.lightboxtoolbar.LightBoxToolBar
   ~fsl.fsleyes.controls.locationpanel.LocationPanel
   ~fsl.fsleyes.controls.lookuptablepanel.LookupTablePanel
   ~fsl.fsleyes.controls.orthoedittoolbar.OrthoEditToolBar
   ~fsl.fsleyes.controls.orthotoolbar.OrthoToolBar
   ~fsl.fsleyes.controls.overlaydisplaypanel.OverlayDisplayPanel
   ~fsl.fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar
   ~fsl.fsleyes.controls.overlayinfopanel.OverlayInfoPanel
   ~fsl.fsleyes.controls.overlaylistpanel.OverlayListPanel
   ~fsl.fsleyes.controls.plotcontrolpanel.PlotControlPanel
   ~fsl.fsleyes.controls.plotlistpanel.PlotListPanel
   ~fsl.fsleyes.controls.powerspectrumcontrolpanel.PowerSpectrumControlPanel
   ~fsl.fsleyes.controls.shellpanel.ShellPanel
   ~fsl.fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel
"""

import atlaspanel
import canvassettingspanel
import clusterpanel
import histogramcontrolpanel
import lightboxtoolbar
import locationpanel
import lookuptablepanel
import melodicclassificationpanel
import orthoedittoolbar
import orthotoolbar
import overlaydisplaypanel
import overlaydisplaytoolbar
import overlayinfopanel
import plotlistpanel
import powerspectrumcontrolpanel
import shellpanel
import timeseriescontrolpanel


AtlasPanel                 = atlaspanel.AtlasPanel
CanvasSettingsPanel        = canvassettingspanel.CanvasSettingsPanel
ClusterPanel               = clusterpanel.ClusterPanel
HistogramControlPanel      = histogramcontrolpanel.HistogramControlPanel
LightBoxToolBar            = lightboxtoolbar.LightBoxToolBar
LocationPanel              = locationpanel.LocationPanel
LookupTablePanel           = lookuptablepanel.LookupTablePanel
MelodicClassificationPanel = melodicclassificationpanel.MelodicClassificationPanel
OrthoEditToolBar           = orthoedittoolbar.OrthoEditToolBar
OrthoToolBar               = orthotoolbar.OrthoToolBar
OverlayDisplayPanel        = overlaydisplaypanel.OverlayDisplayPanel
OverlayDisplayToolBar      = overlaydisplaytoolbar.OverlayDisplayToolBar
OverlayInfoPanel           = overlayinfopanel.OverlayInfoPanel
PlotListPanel              = plotlistpanel.PlotListPanel
PowerSpectrumControlPanel  = powerspectrumcontrolpanel.PowerSpectrumControlPanel
ShellPanel                 = shellpanel.ShellPanel
TimeSeriesControlPanel     = timeseriescontrolpanel.TimeSeriesControlPanel
