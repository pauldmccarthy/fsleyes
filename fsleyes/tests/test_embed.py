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
import fsleyes.gl     as fslgl
import fsleyes.main   as fslmain

import fsleyes.displaycontext.displaycontext as displaycontext
import fsleyes.views.orthopanel as orthopanel

datadir = op.join(op.dirname(__file__), 'testdata')


def test_embed():

    gc.collect()
    idle.idleLoop.reset()

    app = wx.App()
    frame = [wx.Frame(None)]

    ncalls = [0]

    def finish():
        frame[0].Close()
        fslgl.shutdown()
        app.ExitMainLoop()

    def open_fsleyes():
        print('Embedded call', ncalls[0])

        overlayList, displayCtx, fframe = fslmain.embed(
            menu=False, save=False)

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


def test_embed_ownFrame():

    gc.collect()
    idle.idleLoop.reset()

    app = wx.App()
    frame = [wx.Frame(None)]
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    frame[0].SetSizer(sizer)

    panel = [None]

    ncalls = [0]

    def finish():
        frame[0].Close()
        fslgl.shutdown()
        app.ExitMainLoop()

    def reset():
        print('Resetting', ncalls)
        sizer.Remove(0)
        panel[0].destroy()
        panel[0].Destroy()
        panel[0] = None


    def open_fsleyes():
        print('Embedded call', ncalls[0])

        overlayList, displayCtx, fframe = fslmain.embed(
            mkFrame=False, menu=False, save=False)

        assert fframe is None

        img = fslimage.Image(op.join(datadir, '3d'))
        overlayList.append(img)

        cdctx = displaycontext.DisplayContext(
            overlayList,
            displayCtx)

        panel[0] = orthopanel.OrthoPanel(frame[0], overlayList, cdctx, None)
        sizer.Add(panel[0], flag=wx.EXPAND, proportion=1)

        frame[0].Layout()
        frame[0].Refresh()

        ncalls[0] += 1

        wx.CallLater(1500, reset)

        if ncalls[0] < 4:
            wx.CallLater(2500, open_fsleyes)
        else:
            print('Done - closing')
            wx.CallLater(2500, finish)

    wx.CallLater(1000, open_fsleyes)

    frame[0].Show()
    app.MainLoop()

    assert ncalls[0] == 4
