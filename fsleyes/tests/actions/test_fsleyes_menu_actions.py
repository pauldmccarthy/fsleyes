#!/usr/bin/env python
#
# test_fsleyes_menu_actions.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

from unittest import mock

import wx

from fsleyes.tests import (run_with_orthopanel,
                           run_with_fsleyes,
                           realYield,
                           MockFileDialog,
                           mockFSLDIR)

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image

import fsleyes.actions.diagnosticreport as report
import fsleyes.actions.clearsettings    as clearsettings
import fsleyes.actions.updatecheck      as updatecheck
import fsleyes.about                    as aboutdlg
import fsleyes.actions.about            as about


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_about():
    run_with_orthopanel(_test_about)

def _test_about(panel, overlayList, displayCtx):
    panel.frame.menuActions[about.AboutAction]()
    realYield()
    windows = wx.GetTopLevelWindows()
    dlg = [w for w in windows if isinstance(w, aboutdlg.AboutDialog)][0]
    dlg.Close()


def test_report():
    run_with_orthopanel(_test_report)

def _test_report(panel, overlayList, displayCtx):
    overlayList.append(Image(op.join(datadir, '3d')))
    realYield()
    with tempdir(), MockFileDialog() as dlg:
        dlg.ShowModal_retval = wx.ID_OK
        dlg.GetPath_retval   = 'report.txt'
        panel.frame.menuActions[report.DiagnosticReportAction]()
        assert op.exists('report.txt')



def test_clearSettings():
    run_with_orthopanel(_test_clearSettings)

def _test_clearSettings(panel, overlayList, displayCtx):
    class MockDialog(object):
        def __init__(self, *args, **kwargs):
            pass
        def ShowModal(self):
            return wx.ID_YES
        def CentreOnParent(self):
            pass

    with mock.patch('wx.MessageDialog', MockDialog):
        panel.frame.menuActions[clearsettings.ClearSettingsAction]()



def test_updatecheck():
    run_with_fsleyes(_test_updatecheck)

def _test_updatecheck(frame, overlayList, displayCtx):

    uc = frame.menuActions[updatecheck.UpdateCheckAction]

    with tempdir(), \
         mock.patch('fsleyes.version.__version__', '1.0.0'), \
         mock.patch('fsleyes.actions.updatecheck.UrlDialog', mock.MagicMock()):

        with open('version.txt', 'wt') as f:
            f.write('0.10.0')
        with open('version.txt', 'rb') as f:
            with mock.patch('urllib.request.urlopen', return_value=f):
                uc()


def test_UrlDialog():
    run_with_fsleyes(_test_UrlDialog)
def _test_UrlDialog(frame, *a):

    dlg = updatecheck.UrlDialog(frame,
                                'title',
                                'message',
                                urlMsg='url',
                                url='url')

    wx.CallLater(750, dlg.EndModal, wx.ID_OK)
    dlg.ShowModal()


def test_setFSLDIR():
    run_with_fsleyes(_test_setFSLDIR)
def _test_setFSLDIR(frame, overlayList, displayCtx):

    with MockFileDialog(True), mockFSLDIR():
        frame.setFSLDIR()


def test_help():
    run_with_fsleyes(_test_help)
def _test_help(frame, overlayList, displayCtx):

    opened = [None]

    def openPage(page):
        opened[0] = page

    with mock.patch('fsleyes_widgets.utils.webpage.openPage', openPage):
        frame.openHelp()
        assert opened[0] is not None

def test_close():
    run_with_fsleyes(_test_close)
def _test_close(frame, overlayList, displayCtx):
    with mock.patch('fsleyes.frame.FSLeyesFrame.Close',
                    return_val=None):
        frame.closeFSLeyes()
