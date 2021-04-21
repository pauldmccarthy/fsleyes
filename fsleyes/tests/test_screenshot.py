#!/usr/bin/env python
#
# test_screenshot.py - Test fsleyes.actions.screenshot
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path          as op

import fsl.data.image   as fslimage
import fsl.utils.idle   as idle

from fsleyes.tests import (run_with_orthopanel,
                           run_with_lightboxpanel,
                           run_with_scene3dpanel,
                           run_with_timeseriespanel,
                           run_with_histogrampanel,
                           run_with_powerspectrumpanel,
                           tempdir,
                           realYield,
                           compare_images)


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_screenshot(panel, overlayList, displayCtx, stype, imgfile):

    import matplotlib.image           as mplimg
    import fsleyes.actions.screenshot as screenshot
    import fsleyes.views.orthopanel   as orthopanel

    if isinstance(panel, orthopanel.OrthoPanel):
        panel.sceneOpts.showCursor = False
        panel.sceneOpts.showLabels = False

    img = fslimage.Image(op.join(datadir, imgfile))

    overlayList.append(img)

    with tempdir():

        fname = 'test_screenshot_{}.png'.format(stype)

        realYield(100)
        idle.idle(screenshot.screenshot, panel, fname)
        idle.block(10, until=lambda : op.exists(fname))
        realYield()

        bfname     = op.join(datadir, 'test_screenshot_{}.png'.format(stype))
        screenshot = mplimg.imread(fname)
        benchmark  = mplimg.imread(bfname)

        result, diff = compare_images(screenshot, benchmark, 50)

        print('Comparing {} with {}: {}'.format(fname, bfname, diff))

        assert result


def test_screenshot_ortho():
    run_with_orthopanel(_test_screenshot, 'ortho', '3d')

def test_screenshot_lightbox():
    run_with_lightboxpanel(_test_screenshot, 'lightbox', '3d')

def test_screenshot_3d():
    run_with_scene3dpanel(_test_screenshot, '3d', '3d')

def test_screenshot_timeseries():
    run_with_timeseriespanel(_test_screenshot, 'timeseries', '4d')

def test_screenshot_histogram():
    run_with_histogrampanel(_test_screenshot, 'histogram', '4d')

def test_screenshot_powerspectrum():
    run_with_powerspectrumpanel(_test_screenshot, 'powerspectrum', '4d')
