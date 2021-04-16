#!/usr/bin/env python
#
# test_ortho_cropmode.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import numpy as np

import wx

from fsl.data.image import Image

from fsleyes.plugins.profiles.orthocropprofile import OrthoCropProfile

from fsleyes.tests import run_with_orthopanel, realYield, simclick


datadir = op.join(op.dirname(__file__), 'testdata')


def _clickdrag(canvas, profile, startpos, endpos):

    poses = np.linspace(startpos, endpos, 4)

    for i, pos in enumerate(poses):

        xpos   = pos[canvas.opts.xax]
        ypos   = pos[canvas.opts.yax]
        bounds = canvas.opts.displayBounds

        xpos = (xpos) / bounds.xlen
        ypos = (ypos) / bounds.ylen


        print('click', canvas.opts.zax, pos)

        if   i == 0:              handler = profile._cropModeLeftMouseDown
        elif i == len(poses) - 1: handler = profile._cropModeLeftMouseUp
        else:                     handler = profile._cropModeLeftMouseDrag

        handler(None, canvas, (1 - xpos, ypos), pos)
        realYield(10)


def _do_crop(ortho, overlayList, displayCtx, img, roi):

    profile = ortho.currentProfile

    xlo, xhi = roi[0]
    ylo, yhi = roi[1]
    zlo, zhi = roi[2]

    xmax, ymax, zmax = img.shape[:3]

    xmid = (xhi - xlo) / 2
    ymid = (yhi - ylo) / 2
    zmid = (zhi - zlo) / 2

    xcanvas = ortho.getXCanvas()
    ycanvas = ortho.getYCanvas()
    zcanvas = ortho.getZCanvas()
    opts    = ortho.displayCtx.getOpts(img)

    if xlo >= 0:    xlo += 1.5
    else:           xlo -= 1.5
    if ylo >= 0:    ylo += 1.5
    else:           ylo -= 1.5
    if zlo >= 0:    zlo += 1.5
    else:           zlo -= 1.5
    if xhi <= xmax: xhi -= 2.5
    else:           pass
    if yhi <= ymax: yhi -= 2.5
    else:           pass
    if zhi <= zmax: zhi -= 2.5
    else:           pass

    clicks = [
        (xcanvas, [xmid, 0,    zmid], [xmid, ylo,  zmid]),
        (xcanvas, [xmid, ymax, zmid], [xmid, yhi,  zmid]),
        (ycanvas, [xmid, ymid, 0   ], [xmid, ymid, zlo ]),
        (ycanvas, [xmid, ymid, zmax], [xmid, ymid, zhi]),
        (zcanvas, [0,    ymid, zmid], [xlo,  ymid, zmid]),
        (zcanvas, [xmax, ymid, zmid], [xhi,  ymid, zmid])]

    for canvas, startpos, endpos in clicks:
        startpos = np.array(startpos)
        endpos   = np.array(endpos)
        startpos = opts.transformCoords(startpos, 'voxel', 'display')
        endpos   = opts.transformCoords(endpos,   'voxel', 'display')
        _clickdrag(canvas, profile, startpos, endpos)
        realYield(10)

    got = np.array(profile.cropBox[:]).reshape(-1)
    exp = np.array(roi).reshape(-1)

    assert np.all(got == exp)


def _test_crop_interaction(ortho, overlayList, displayCtx):

    data = np.random.randint(1, 65536, (30, 30, 30))
    img  = Image(data)
    overlayList[:] = [img]
    displayCtx.displaySpace = img

    realYield()
    ortho.profileManager.activateProfile(OrthoCropProfile)
    realYield(30)

    _do_crop(ortho, overlayList, displayCtx, img, [(5, 25), (5, 25), (5, 25)])

    ortho.sceneOpts.zoom = 50
    realYield(5)
    _do_crop(ortho, overlayList, displayCtx, img, [(-2, 32), (-2, 32), (-2, 32)])


def test_crop():
    run_with_orthopanel(_test_crop_interaction)
