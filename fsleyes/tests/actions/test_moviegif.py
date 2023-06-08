#!/usr/bin/env python

import numpy as np

import fsl.transform.affine     as affine
import fsleyes.actions.moviegif as moviegif


def test_MovieContext():

    def test_context(ctx, frames):
        for i, f in enumerate(frames):

            if ctx.is3d: expf = affine.rmsdev(frames[0], f)
            else:        expf = f

            exp = (expf, i == (len(frames) - 1))
            got =  ctx.processFrame(f)
            assert np.isclose(exp[0], got[0])
            assert exp[1] == got[1]
            ctx.addFrame(expf, None)

    ctx    = moviegif.MovieContext(False)
    frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 0]
    test_context(ctx, frames)

    # integer frames
    ctx    = moviegif.MovieContext(False)
    frames = [5, 6, 7, 8, 9, 10, 0, 1, 2, 3, 4, 5]
    test_context(ctx, frames)

    # non-integer frames
    ctx    = moviegif.MovieContext(False)
    frames = [5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    test_context(ctx, frames)

    # inconsistent frame delta
    ctx    = moviegif.MovieContext(False)
    frames = [5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 0, 1, 2, 3, 4, 5, 6]
    test_context(ctx, frames)

    # 3D rotation
    ctx    = moviegif.MovieContext(True)
    frames = np.linspace(0, np.pi * 2, 20)
    frames = [affine.axisAnglesToRotMat(f, 0, 0) for f in frames]
    test_context(ctx, frames)

    ctx    = moviegif.MovieContext(True)
    frames = frames[10:] + frames[:10] + [frames[10]]
    test_context(ctx, frames)
