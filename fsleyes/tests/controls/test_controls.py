#!/usr/bin/env python
#
# test_controls.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

from fsl.data.image import Image

from fsleyes.controls.orthotoolbar              import OrthoToolBar
from fsleyes.controls.lightboxtoolbar           import LightBoxToolBar
from fsleyes.controls.scene3dtoolbar            import Scene3DToolBar
from fsleyes.controls.overlaydisplaypanel       import OverlayDisplayPanel
from fsleyes.controls.overlaydisplaytoolbar     import OverlayDisplayToolBar
from fsleyes.controls.canvassettingspanel       import CanvasSettingsPanel
from fsleyes.controls.locationpanel             import LocationPanel
from fsleyes.controls.overlaylistpanel          import OverlayListPanel
from fsleyes.controls.histogramcontrolpanel     import HistogramControlPanel
from fsleyes.controls.histogramtoolbar          import HistogramToolBar
from fsleyes.controls.powerspectrumcontrolpanel import \
    PowerSpectrumControlPanel
from fsleyes.controls.powerspectrumtoolbar      import PowerSpectrumToolBar
from fsleyes.controls.timeseriescontrolpanel    import TimeSeriesControlPanel
from fsleyes.controls.timeseriestoolbar         import TimeSeriesToolBar
from fsleyes.controls.plotlistpanel             import PlotListPanel

from fsleyes.plugins.controls.lookuptablepanel import LookupTablePanel
from fsleyes.plugins.controls.clusterpanel     import ClusterPanel
from fsleyes.plugins.controls.overlayinfopanel import OverlayInfoPanel
from fsleyes.plugins.controls.atlaspanel       import AtlasPanel
from fsleyes.plugins.controls.annotationpanel  import AnnotationPanel
from fsleyes.plugins.controls.filetreepanel    import FileTreePanel
from fsleyes.plugins.controls.melodicclassificationpanel \
    import MelodicClassificationPanel

from fsleyes.tests import (run_with_scene3dpanel,
                           run_with_orthopanel,
                           run_with_lightboxpanel,
                           run_with_timeseriespanel,
                           run_with_histogrampanel,
                           run_with_powerspectrumpanel,
                           realYield)


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_controls_OrthoPanel():
    run_with_orthopanel(_test_controls_OrthoPanel)

def _test_controls_OrthoPanel(view, overlayList, displayCtx):

    overlayList.append(Image(op.join(datadir, '3d')))
    realYield(25)

    ctrls = (OrthoToolBar, OverlayDisplayToolBar,
             OverlayDisplayPanel, CanvasSettingsPanel,
             LocationPanel, OverlayListPanel, LookupTablePanel,
             ClusterPanel, OverlayInfoPanel, AtlasPanel, AnnotationPanel,
             FileTreePanel, MelodicClassificationPanel)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)


def test_controls_Scene3DPanel():
    run_with_scene3dpanel(_test_controls_Scene3DPanel)

def _test_controls_Scene3DPanel(view, overlayList, displayCtx):

    overlayList.append(Image(op.join(datadir, '3d')))
    realYield(25)

    ctrls = (Scene3DToolBar, OverlayDisplayToolBar,
             OverlayDisplayPanel, CanvasSettingsPanel,
                 LocationPanel, OverlayListPanel, LookupTablePanel,
             ClusterPanel, OverlayInfoPanel, AtlasPanel, FileTreePanel,
             MelodicClassificationPanel)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)


def test_controls_LightBoxPanel():
    run_with_lightboxpanel(_test_controls_LightBoxPanel)

def _test_controls_LightBoxPanel(view, overlayList, displayCtx):

    overlayList.append(Image(op.join(datadir, '3d')))
    realYield(25)

    ctrls = (LightBoxToolBar, OverlayDisplayToolBar,
             OverlayDisplayPanel, CanvasSettingsPanel,
             LocationPanel, OverlayListPanel, LookupTablePanel,
             ClusterPanel, OverlayInfoPanel, AtlasPanel,
             FileTreePanel, MelodicClassificationPanel)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)


def test_controls_TimeSeriesPanel():
    run_with_timeseriespanel(_test_controls_TimeSeriesPanel)

def _test_controls_TimeSeriesPanel(view, overlayList, displayCtx):

    overlayList.append(Image(op.join(datadir, '4d')))
    realYield(25)

    ctrls = (TimeSeriesToolBar, TimeSeriesControlPanel,
             PlotListPanel, OverlayListPanel)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)


def test_controls_HistogramPanel():
    run_with_histogrampanel(_test_controls_HistogramPanel)

def _test_controls_HistogramPanel(view, overlayList, displayCtx):

    overlayList.append(Image(op.join(datadir, '4d')))
    realYield(25)

    ctrls = (HistogramToolBar, HistogramControlPanel,
             PlotListPanel, OverlayListPanel)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)


def test_controls_PowerSpectrumPanel():
    run_with_powerspectrumpanel(_test_controls_PowerSpectrumPanel)

def _test_controls_PowerSpectrumPanel(view, overlayList, displayCtx):

    overlayList.append(Image(op.join(datadir, '4d')))
    realYield(25)

    ctrls = (PowerSpectrumToolBar, PowerSpectrumControlPanel,
             PlotListPanel, OverlayListPanel)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)

    for ctrl in ctrls:
        view.togglePanel(ctrl)
        realYield(25)
