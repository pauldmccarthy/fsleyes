#!/usr/bin/env python
#
# moviegif.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            os
import            shutil
import            tempfile

import          PIL
import          wx
import numpy as np

import fsl.utils.idle                 as idle
import fsl.utils.transform            as transform
import fsl.utils.settings             as fslsettings
import fsleyes_widgets.utils.progress as progress
from   fsleyes_widgets import            isalive

from . import base

import fsleyes.strings            as strings
import fsleyes.actions.screenshot as screenshot
import fsleyes.views.scene3dpanel as scene3dpanel


class MovieGifAction(base.Action):
    """
    """

    def __init__(self, overlayList, displayCtx, panel):
        """Create a ``MovieGifAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg panel:       The :class:`.CanvasPanel` to generate the animated
                          GIF for.
        """

        base.Action.__init__(self, self.__doMakeGif)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__panel       = panel

        # TODO disable when appropriate (e.g. .gif output not supported,
        #      movie settings not compatible with overlay, etc)


    def __doMakeGif(self):

        lastDirSetting = 'fsleyes.actions.screenshot.lastDir'
        filename       = 'movie.gif'
        fromDir        = fslsettings.read(lastDirSetting, os.getcwd())

        dlg = wx.FileDialog(self.__panel,
                            message=strings.messages[self, 'movieGif'],
                            defaultDir=fromDir,
                            defaultFile=filename,
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filename = dlg.GetPath()
        self.__progdlg  = progress.Bounce(
            'Generating GIF',
            'Generating GIF',
            style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT,
            parent=self.__panel)

        def update(frame):
            if isalive(self.__progdlg):
                self.__progdlg.DoBounce('Saved frame {}...'.format(frame))
                return not self.__progdlg.WasCancelled()
            else:
                return False

        def finish():
            if isalive(self.__progdlg):
                self.__progdlg.Hide()
                self.__progdlg.Close()
            self.__progdlg = None

        # TODO show progress dialog
        # TODO prompt user to select axis/delay/limits?
        self.__progdlg.Show()
        makeGif(self.__overlayList,
                self.__displayCtx,
                self.__panel,
                filename,
                progfunc=update,
                onfinish=finish)


def makeGif(overlayList,
            displayCtx,
            panel,
            filename,
            progfunc=None,
            onfinish=None):
    """

    .. note:: This function will return immediately, as the animated GIF is
              generated on the ``wx`` :mod:`.idle` loop
    """

    def defaultProgFunc(frame):
        return True

    if progfunc is None:
        progfunc = defaultProgFunc

    overlay = displayCtx.getSelectedOverlay()
    opts    = displayCtx.getOpts(overlay)
    tempdir = tempfile.mkdtemp()
    is3d    = isinstance(panel, scene3dpanel.Scene3DPanel) and \
              panel.movieAxis != 3

    class Context(object):
        pass

    ctx           = Context()
    ctx.cancelled = False
    ctx.images    = []
    ctx.frames    = []

    class Finished(Exception):
        pass

    class Cancelled(Exception):
        pass

    def finalise(ctx):
        if not ctx.cancelled and len(ctx.images) > 0:
            ctx.images[0].save(filename,
                               format='gif',
                               save_all=True,
                               append_images=ctx.images[1:])
        shutil.rmtree(tempdir)

        if onfinish is not None:
            onfinish()

    def ready():
        globjs = [c.getGLObject(o)
                  for c in panel.getGLCanvases()
                  for o in overlayList]
        globjs = [g for g in globjs if g is not None]
        return all([g.ready() for g in globjs])

    def captureFrame(ctx):
        try:
            realCaptureFrame(ctx)
            idle.idleWhen(captureFrame, ready, ctx, after=0.1)
            panel.doMovieUpdate(overlay, opts)

        except Finished:
            finalise(ctx)

        except (Cancelled, Exception) as e:
            ctx.cancelled = True
            finalise(ctx)

    def realCaptureFrame(ctx):

        idx   = len(ctx.frames)
        fname = op.join(tempdir, '{}.gif'.format(idx))

        frame = panel.getMovieFrame(overlay, opts)

        if not progfunc(idx):
            raise Cancelled()

        # The 3D X/Y/Z movie mode performs
        # rotations, rather than moving the
        # display location through the X/Y/Z
        # axes. The "frame" returned by
        # getMovieFrame is a rotation matrix.
        # We convert these rotation matrices
        # into rms-deviations (average
        # deviation of the current frame from
        # the starting frame), which has an
        # inverted "V"-shaped wave form as the
        # scene is rotated 360 degrees. So
        # we continue capturing frames until
        # the rmsdev of the current frame is:
        #
        #   - close to 0 (i.e. very similar to
        #     the rotation matrix of the starting
        #     frame), and
        #
        #   - less than the most recent frame (i.e.
        #     has rotated past 180 degrees, and is
        #     rotating back twoards the starting
        #     point)
        if is3d:

            if len(ctx.frames) == 0:
                ctx.startFrame = frame

            # normalise the rotmat for this
            # frame to the rms difference
            # from the starting rotmat
            frame = _rmsdev(ctx.startFrame, frame)

            # Keep capturing frames until we
            # have performed a full 360 degree
            # rotation (rmsdev of current
            # frame is decreasing towards 0)
            if len(ctx.frames) > 1    and \
               frame < ctx.frames[-1] and \
               abs(frame) < 0.1:
                raise Finished()

        # All other movie frames have a range
        # (fmin, fmax) and start at some arbitrary
        # point within this range. We capture frames
        # until a full loop through this range has
        # been completed.
        else:

            # Have we looped back to fmin?
            ctx.looped = getattr(ctx, 'looped', False)
            if not ctx.looped          and \
               len(ctx.frames) > 1 and \
               frame < ctx.frames[-1]:
                ctx.looped = True

            # We have done one full loop, and
            # have reached the starting frame.
            if ctx.looped          and \
               len(ctx.frames) > 1 and \
               frame >= ctx.frames[0]:
                raise Finished()

        screenshot.screenshot(panel, fname)
        ctx.images.append(PIL.Image.open(fname))
        ctx.frames.append(frame)

    idle.idleWhen(captureFrame, ready, ctx, after=0.1)


def _rmsdev(T1, T2, R=None, xc=None):
    """Calculates the RMS deviation of the given affine transforms ``T1`` and
    ``T2``.

    See FMRIB technical report TR99MJ1, available at:

    https://www.fmrib.ox.ac.uk/datasets/techrep/

    .. warning:: This function will be moved somewhere else in the future. Do
                 not depend on it.
    """

    if R is None:
        R = 1

    if xc is None:
        xc = np.zeros(3)

    # rotations only
    if T1.shape == (3, 3):
        M = np.dot(T2, transform.invert(T1)) - np.eye(3)
        A = M[:3, :3]
        t = np.zeros(3)

    # full affine
    else:
        M = np.dot(T2, transform.invert(T1)) - np.eye(4)
        A = M[:3, :3]
        t = M[:3,  3]

    Axc = np.dot(A, xc)

    erms = np.dot((t + Axc).T, t + Axc)
    erms = 0.2 * R ** 2 * np.dot(A.T, A).trace() + erms
    erms = np.sqrt(erms)

    return erms
