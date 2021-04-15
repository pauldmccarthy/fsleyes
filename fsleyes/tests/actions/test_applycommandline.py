#!/usr/bin/env python
#
# test_applycommandline.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

try:
    from unittest import mock
except ImportError:
    import mock

import os
import os.path as op

import wx

import numpy as np

from   fsl.utils.tempdir import tempdir
import fsl.data.image        as fslimage

import fsleyes.actions.applycommandline as applycommandline
from fsleyes.tests import (run_with_orthopanel,
                           realYield,
                           waitUntilIdle)


def test_applyCommandLine_overlayOnly():
    run_with_orthopanel(_test_applyCommandLine_overlayOnly)
def _test_applyCommandLine_overlayOnly(panel, overlayList, displayCtx):

    displayCtx = panel.displayCtx
    panel.sceneOpts.layout = 'horizontal'

    with tempdir():
        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        img.save('image.nii.gz')

        applycommandline.applyCommandLineArgs(
            overlayList,
            panel.displayCtx,
            ['-lo', 'vertical',
             'image.nii.gz', '-b', '75', '-c', '25', '-g', '-0.5'],
            blocking=True)

        assert len(overlayList) == 1
        assert np.all(overlayList[0][:] == img[:])
        img = overlayList[0]
        assert displayCtx.getDisplay(img).brightness ==  75
        assert displayCtx.getDisplay(img).contrast   ==  25
        assert displayCtx.getOpts(   img).gamma      == -0.5

        assert panel.sceneOpts.layout == 'horizontal'


def test_applyCommandLine_sceneOnly():
    run_with_orthopanel(_test_applyCommandLine_sceneOnly)
def _test_applyCommandLine_sceneOnly(panel, overlayList, displayCtx):

    panel.sceneOpts.layout = 'horizontal'

    with tempdir():
        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        img.save('image.nii.gz')

        applycommandline.applyCommandLineArgs(
            overlayList,
            panel.displayCtx,
            ['-lo', 'vertical',
             'image.nii.gz', '-b', '75', '-c', '25', '-g', '-0.5'],
            panel=panel,
            applyOverlayArgs=False)

        # scene args are applied asynchronously
        waitUntilIdle()

        assert len(overlayList) == 0
        assert panel.sceneOpts.layout == 'vertical'


def test_applyCommandLine():
    run_with_orthopanel(_test_applyCommandLine)
def _test_applyCommandLine(panel, overlayList, displayCtx):

    displayCtx = panel.displayCtx
    panel.sceneOpts.layout = 'horizontal'

    with tempdir():
        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        img.save('image.nii.gz')

        applycommandline.applyCommandLineArgs(
            overlayList,
            panel.displayCtx,
            ['-lo', 'vertical',
             'image.nii.gz', '-b', '75', '-c', '25', '-g', '-0.5'],
            panel=panel,
            blocking=True)

        # scene args are applied asynchronously
        waitUntilIdle()

        assert len(overlayList) == 1
        assert np.all(overlayList[0][:] == img[:])
        img = overlayList[0]
        assert displayCtx.getDisplay(img).brightness ==  75
        assert displayCtx.getDisplay(img).contrast   ==  25
        assert displayCtx.getOpts(   img).gamma      == -0.5
        assert panel.sceneOpts.layout == 'vertical'


def test_applyCommandLine_baseDir():
    run_with_orthopanel(_test_applyCommandLine)
def _test_applyCommandLine_baseDir(panel, overlayList, displayCtx):

    displayCtx = panel.displayCtx

    with tempdir():
        basedir = op.join(*'sub/dir/to/test/base/dir/'.split('/'))
        os.makedirs(basedir)

        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        img.save(op.join(basedir, 'image.nii.gz'))

        applycommandline.applyCommandLineArgs(
            overlayList,
            panel.displayCtx,
            ['-lo', 'vertical',
             'image.nii.gz', '-b', '75', '-c', '25', '-g', '-0.5'],
            baseDir=basedir,
            panel=panel,
            blocking=True)

        # scene args are applied asynchronously
        waitUntilIdle()

        assert len(overlayList) == 1
        assert np.all(overlayList[0][:] == img[:])
        img = overlayList[0]
        assert displayCtx.getDisplay(img).brightness ==  75
        assert displayCtx.getDisplay(img).contrast   ==  25
        assert displayCtx.getOpts(   img).gamma      == -0.5
        assert panel.sceneOpts.layout == 'vertical'


def test_ApplyCommandLineAction():
    run_with_orthopanel(_test_ApplyCommandLineAction)
def _test_ApplyCommandLineAction(panel, overlayList, displayCtx):

    displayCtx = panel.displayCtx
    panel.sceneOpts.layout = 'horizontal'

    class TextEditDialog(object):
        ShowModal_return = wx.ID_OK
        GetText_return   = ''
        def __init__(self, *a, **kwa):
            pass
        def CentreOnParent(self):
            pass
        def ShowModal(self):
            return TextEditDialog.ShowModal_return
        def GetText(self):
            return TextEditDialog.GetText_return

    with tempdir(), mock.patch('fsleyes_widgets.dialog.TextEditDialog',
                               TextEditDialog):


        act = applycommandline.ApplyCommandLineAction(overlayList,
                                                      displayCtx,
                                                      panel)

        img = fslimage.Image(np.random.randint(1, 255, (20, 20, 20)))
        img.save('image.nii.gz')

        TextEditDialog.ShowModal_return = wx.ID_CANCEL
        act()
        waitUntilIdle()
        assert len(overlayList) == 0

        args = '-lo vertical image.nii.gz -b 75 -c 25 -g -0.5'

        TextEditDialog.ShowModal_return = wx.ID_OK
        TextEditDialog.GetText_return = args
        act()
        waitUntilIdle()

        assert len(overlayList) == 1
        assert np.all(overlayList[0][:] == img[:])
        img = overlayList[0]
        assert displayCtx.getDisplay(img).brightness ==  75
        assert displayCtx.getDisplay(img).contrast   ==  25
        assert displayCtx.getOpts(   img).gamma      == -0.5
        assert panel.sceneOpts.layout == 'vertical'
