#!/usr/bin/env python
#
# test_updatecheck.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock

import wx

import fsleyes.actions.updatecheck as updatecheck


from fsleyes.tests import run_with_fsleyes, realYield


def test_UpdateCheckAction():
    run_with_fsleyes(_test_UpdateCheckAction)


def _test_UpdateCheckAction(frame, overlayList, displayCtx):

    def ok():
        for win in wx.GetTopLevelWindows():
            if type(win).__name__ == 'UrlDialog':
                win.EndModal(wx.ID_OK)
                win.Destroy()
                break

    act = updatecheck.UpdateCheckAction(overlayList, displayCtx)
    wx.CallLater(500, ok)
    act()

    realYield()

    with mock.patch('fsleyes.version.__version__', '0.0.1'):
        act = updatecheck.UpdateCheckAction(overlayList, displayCtx)
        wx.CallLater(500, ok)
        act()
