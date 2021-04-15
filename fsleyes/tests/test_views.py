#!/usr/bin/env python
#
# test_views.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import fsl.data.image as fslimage

from fsleyes.tests import run_with_fsleyes, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_view(frame, overlayList, displayCtx, vtype):

    img = fslimage.Image(op.join(datadir, '4d'))
    overlayList.append(img)

    frame.addViewPanel(vtype)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])

    realYield(100)


def test_orthopanel():
    from fsleyes.views.orthopanel import OrthoPanel
    run_with_fsleyes(_test_view, OrthoPanel)


def test_lightboxpanel():
    from fsleyes.views.lightboxpanel import LightBoxPanel
    run_with_fsleyes(_test_view, LightBoxPanel)


def test_scene3dpanel():
    from fsleyes.views.scene3dpanel import Scene3DPanel
    run_with_fsleyes(_test_view, Scene3DPanel)


def test_timeseriespanel():
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    run_with_fsleyes(_test_view, TimeSeriesPanel)


def test_histogrampanel():
    from fsleyes.views.histogrampanel import HistogramPanel
    run_with_fsleyes(_test_view, HistogramPanel)


def test_powerspectrumpanel():
    from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
    run_with_fsleyes(_test_view, PowerSpectrumPanel)


def test_shellpanel():
    from fsleyes.views.shellpanel import ShellPanel
    run_with_fsleyes(_test_view, ShellPanel)
