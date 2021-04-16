#!/usr/bin/env python
#


import os.path as op
import fsleyes.frame as fslframe
from fsleyes.tests import run_with_orthopanel, realYield


def test_frame():
    pass


def test_droptarget():
    run_with_orthopanel(_test_droptarget)


def _test_droptarget(panel, overlayList, displayCtx):

    datadir = op.join(op.dirname(__file__), 'testdata')
    filename = op.join(datadir, '3d.nii.gz')
    dt = fslframe.OverlayDropTarget(overlayList, displayCtx)
    dt.OnDropFiles(0, 0, [filename])
    realYield(50)
    assert overlayList[0].dataSource == filename
