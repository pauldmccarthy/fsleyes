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


datadir = op.join(op.dirname(__file__), 'testdata')


def test_embed():

    gc.collect()
    idle.idleLoop.reset()

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

    ncalls = [0]

    def finish():
        frame[0].Close()
        app.ExitMainLoop()

    def open_fsleyes():
        print('Embedded call', ncalls[0])

        overlayList, displayCtx, fframe = fslmain.embed(
            frame[0], menu=False, save=False)

        img = fslimage.Image(op.join(datadir, '3d'))
        fframe.addOrthoPanel()
        overlayList.append(img)
        fframe.Show()
        ncalls[0] += 1

        wx.CallLater(1500, fframe.Close)
        fframe = None
        if ncalls[0] < 4:
            wx.CallLater(2500, open_fsleyes)
        else:
            print('Done - closing')
            wx.CallLater(1500, finish)

    wx.CallLater(1000, open_fsleyes)

    frame[0].Show()
    app.MainLoop()

    assert ncalls[0] == 4
