#!/usr/bin/env python
#
# test_report.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import wx

from . import run_with_orthopanel, realYield, MockFileDialog

from fsl.utils.tempdir import tempdir
from fsl.data.image import Image
import fsleyes.actions.diagnosticreport as report

datadir = op.join(op.dirname(__file__), 'testdata')


def _test_report(panel, overlayList, displayCtx):
    overlayList.append(Image(op.join(datadir, '3d')))
    realYield()

    with tempdir(), MockFileDialog() as dlg:
        dlg.ShowModal.retval = wx.ID_OK
        dlg.GetPath.retval   = 'report.txt'
        panel.frame.menuActions[report.DiagnosticReportAction]()

        assert op.exists('report.txt')


def test_report():
    run_with_orthopanel(_test_report)
