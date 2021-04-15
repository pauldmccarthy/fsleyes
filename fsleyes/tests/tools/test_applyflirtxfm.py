#!/usr/bin/env python
#
# test_applyflirtxfm.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op
from unittest import mock
from contextlib import contextmanager
import numpy as np

import wx
import fsleyes.plugins.tools.applyflirtxfm as applyflirtxfm

from fsl.utils.tempdir import tempdir
from fsl.data.image import Image
from fsl.transform.affine import compose, concat
from fsl.transform.flirt import flirtMatrixToSform

from fsleyes.tests import (run_with_orthopanel,
                           realYield,
                           MockFileDialog,
                           simclick)

def random_affine():
    return compose(np.random.randint(1, 10, 3),
                   np.random.randint(-50, 50, 3),
                   np.random.randint(-3, 3, 3))

def random_image():
    shape = np.random.randint(10, 50, 3)
    aff   = random_affine()
    return Image(np.random.random(shape), xform=aff)


def test_calculateTransform():
    run_with_orthopanel(_test_calculateTransform)

def _test_calculateTransform(panel, overlayList, displayCtx):
    src = random_image()
    ref = random_image()
    v2w = random_affine()

    exp = concat(ref.getAffine('fsl', 'world'),
                 v2w,
                 src.getAffine('voxel', 'fsl'))

    with tempdir():
        ref.save('ref.nii')
        np.savetxt('mat.mat', v2w)
        got = applyflirtxfm.calculateTransform(
            src, overlayList, displayCtx, 'mat.mat', 'ref.nii')

    assert np.all(np.isclose(exp, got))


class MockFlirtFileDialog(object):

    ShowModalRet     = wx.ID_OK
    GetAffineTypeRet = None
    GetMatFileRet    = None
    GetRefFileRet    = None

    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        return MockFlirtFileDialog.ShowModalRet

    def Layout(self):
        pass

    def Fit(self):
        pass

    def CentreOnParent(self):
        pass

    def GetAffineType(self):
        return MockFlirtFileDialog.GetAffineTypeRet

    def GetMatFile(self):
        return MockFlirtFileDialog.GetMatFileRet

    def GetRefFile(self):
        return MockFlirtFileDialog.GetRefFileRet


@contextmanager
def mockdir(contents):
    with tempdir():
        for c in contents:
            dirname = op.dirname(c)
            if dirname != '' and not op.exists(dirname):
                os.makedirs(dirname)
            with open(c, 'wt') as f:
                pass
        yield


def test_promptForFlirtFiles():
    run_with_orthopanel(_test_promptForFlirtFiles)

def _test_promptForFlirtFiles(panel, overlayList, displayCtx):

    ovl = random_image()
    overlayList.append(ovl)
    realYield()

    with mock.patch('fsleyes.plugins.tools.applyflirtxfm.FlirtFileDialog',
                    MockFlirtFileDialog):
        MockFlirtFileDialog.ShowModalRet = wx.ID_CANCEL
        got = applyflirtxfm.promptForFlirtFiles(
            panel, ovl, overlayList, displayCtx)
        assert got == (None, None, None)

        MockFlirtFileDialog.ShowModalRet     = wx.ID_OK
        MockFlirtFileDialog.GetAffineTypeRet = 'flirt'
        MockFlirtFileDialog.GetMatFileRet    = 'mat.mat'
        MockFlirtFileDialog.GetRefFileRet    = 'ref.nii'
        got = applyflirtxfm.promptForFlirtFiles(
            panel, ovl, overlayList, displayCtx)
        assert got == ('flirt', 'mat.mat', 'ref.nii')


def test_guessFlirtFiles():
    run_with_orthopanel(_test_guessFlirtFiles)

def _test_guessFlirtFiles(panel, overlayList, displayCtx):

    assert applyflirtxfm.guessFlirtFiles('image.nii') == (None, None)

    featfiles = [
        'analysis.feat/filtered_func_data.nii.gz',
        'analysis.feat/example_func.nii.gz',
        'analysis.feat/struct.nii.gz',
        'analysis.feat/struct_brain.nii.gz',
        'analysis.feat/design.fsf',
        'analysis.feat/design.con',
        'analysis.feat/design.mat',
        'analysis.feat/reg/example_func2highres.mat',
        'analysis.feat/reg/highres2standard.mat',
        'analysis.feat/reg/highres.nii.gz',
        'analysis.feat/reg/standard.nii.gz']

    melfiles = [
        'analysis.ica/melodic_IC.nii.gz',
        'analysis.ica/melodic_mix',
        'analysis.ica/melodic_FTmix',
        'analysis.ica/reg/example_func2highres.mat',
        'analysis.ica/reg/highres2standard.mat',
        'analysis.ica/reg/highres.nii.gz',
        'analysis.ica/reg/standard.nii.gz']

    with mockdir(featfiles):
        got = applyflirtxfm.guessFlirtFiles('analysis.feat/filtered_func_data.nii.gz')
        assert got == ('analysis.feat/reg/example_func2highres.mat',
                       'analysis.feat/reg/highres.nii.gz')
        got = applyflirtxfm.guessFlirtFiles('analysis.feat/struct.nii.gz')
        assert got == ('analysis.feat/reg/highres2standard.mat',
                       'analysis.feat/reg/standard.nii.gz')
    with mockdir(melfiles):
        got = applyflirtxfm.guessFlirtFiles('analysis.ica/mean_func.nii.gz')
        assert got == ('analysis.ica/reg/example_func2highres.mat',
                       'analysis.ica/reg/highres.nii.gz')
        got = applyflirtxfm.guessFlirtFiles('analysis.ica/struct.nii.gz')
        assert got == ('analysis.ica/reg/highres2standard.mat',
                       'analysis.ica/reg/standard.nii.gz')



def test_FlirtFileDialog():
    run_with_orthopanel(_test_FlirtFileDialog)

def _test_FlirtFileDialog(panel, overlayList, displayCtx):

    sim = wx.UIActionSimulator()

    contents = ['func.nii.gz',
                'struct.nii.gz',
                'func2struct.mat']

    with MockFileDialog() as mdlg, mockdir(contents):

        dlg = applyflirtxfm.FlirtFileDialog(panel, 'func.nii')
        simclick(sim, dlg.cancel)

        dlg = applyflirtxfm.FlirtFileDialog(panel, 'func.nii')

        dlg.affType.SetSelection(0)
        dlg._FlirtFileDialog__onAffType(None)

        mdlg.GetPath_retval = 'struct.nii.gz'
        dlg._FlirtFileDialog__onRefFileButton(None)

        mdlg.GetPath_retval = 'func2struct.mat'
        dlg._FlirtFileDialog__onMatFileButton(None)

        simclick(sim, dlg.ok)
        assert dlg.GetAffineType() == 'flirt'
        assert dlg.GetMatFile()    == op.abspath('func2struct.mat')
        assert dlg.GetRefFile()    == op.abspath('struct.nii.gz')


def test_ApplyFlirtXfmAction():
    run_with_orthopanel(_test_ApplyFlirtXfmAction)

def _test_ApplyFlirtXfmAction(panel, overlayList, displayCtx):
    with mock.patch('fsleyes.plugins.tools.applyflirtxfm.FlirtFileDialog',
                    MockFlirtFileDialog), tempdir():

        act = applyflirtxfm.ApplyFlirtXfmAction(
            overlayList, displayCtx, panel.frame)
        src = random_image()
        ref = random_image()
        v2w = random_affine()

        expv2w = flirtMatrixToSform(v2w, src, ref)

        overlayList.append(src)
        realYield()

        ref.save('ref.nii')
        np.savetxt('mat.mat', v2w)

        srcv2w = np.copy(src.voxToWorldMat)

        MockFlirtFileDialog.ShowModalRet = wx.ID_CANCEL
        act()
        assert np.all(np.isclose(src.voxToWorldMat, srcv2w))

        MockFlirtFileDialog.ShowModalRet     = wx.ID_OK
        MockFlirtFileDialog.GetAffineTypeRet = 'flirt'
        MockFlirtFileDialog.GetMatFileRet    = 'mat.mat'
        MockFlirtFileDialog.GetRefFileRet    = 'ref.nii'
        act()
        realYield()
        assert np.all(np.isclose(src.voxToWorldMat, expv2w))
