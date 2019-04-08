#!/usr/bin/env python


from unittest import mock

import wx

import fsl.utils.tempdir as tempdir

import fsleyes.actions.updatecheck as updatecheck

from . import run_with_fsleyes, simclick


def test_updatecheck():
    run_with_fsleyes(_test_updatecheck)

def _test_updatecheck(panel, displayCtx, overlayList):

    uc = updatecheck.UpdateCheckAction()

    with tempdir.tempdir(), \
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

    sim = wx.UIActionSimulator()
    dlg = updatecheck.UrlDialog(frame,
                                'title',
                                'message',
                                urlMsg='url',
                                url='url')

    wx.CallLater(750, simclick, sim, dlg.ok)
    dlg.ShowModal()
