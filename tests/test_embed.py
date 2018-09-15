#!/usr/bin/env python
#
# test_embed.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import gc
import os.path as op

import wx

import fsl.data.image as fslimage
import fsl.utils.idle as idle
import fsleyes.main   as fslmain

from tests import simclick


datadir = op.join(op.dirname(__file__), 'testdata')


def test_embed():

    gc.collect()
    idle.idleReset()

    app = wx.App()
    frame = [wx.Frame(None)]
    panel = wx.Panel(frame[0])
    btn = wx.Button(panel)
    btn.SetLabel('Click to open FSLeyes')
    fsizer = wx.BoxSizer(wx.VERTICAL)
    frame[0].SetSizer(fsizer)
    fsizer.Add(panel, flag=wx.EXPAND)

    psizer = wx.BoxSizer(wx.VERTICAL)
    panel.SetSizer(psizer)
    psizer.Add(btn, flag=wx.EXPAND)

    sim    = wx.UIActionSimulator()
    ncalls = [0]

    def finish():
        frame[0].Close()
        app.ExitMainLoop()

    def embedded(overlayList, displayCtx, fframe):

        print('Embedded call', ncalls[0])

        img = fslimage.Image(op.join(datadir, '3d'))
        fframe.addOrthoPanel()
        overlayList.append(img)
        fframe.Show()
        ncalls[0] += 1

        wx.CallLater(1500, fframe.Close)
        fframe = None
        if ncalls[0] < 4:
            wx.CallLater(2500, simclick, sim, btn)
        else:
            print('Done - closing')
            wx.CallLater(1500, finish)

    def open_fsleyes(ev):
        fslmain.embed(frame[0],
                      callback=embedded,
                      menu=False,
                      save=False)

    btn.Bind(wx.EVT_BUTTON, open_fsleyes)

    wx.CallLater(1000, simclick, sim, btn)

    frame[0].Show()
    app.MainLoop()

    assert ncalls[0] == 4
