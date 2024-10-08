#!/usr/bin/env python
#
# moviegif.py - The MovieGifAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MovieGifAction`, which allows the user
to save animated gifs. The :func:`makeGif` function can also be used to
programmatically generate animated gifs.
"""


import os.path as op
import            os
import            shutil
import            tempfile

import            PIL
import            wx
import numpy   as np

import fsl.utils.idle                 as idle
import fsl.transform.affine           as affine
import fsl.utils.settings             as fslsettings
import fsleyes_widgets.utils.progress as progress
from   fsleyes_widgets import            isalive

from . import base

import fsleyes.strings            as strings
import fsleyes.actions.screenshot as screenshot
import fsleyes.views.scene3dpanel as scene3dpanel


class MovieGifAction(base.Action):
    """The ``MovieGifAction`` allows the user to save an animated gif of the
    currently selected overlay in a :class:`.CanvasPanel`, according to the
    current movie mode settings.
    """

    def __init__(self, overlayList, displayCtx, panel):
        """Create a ``MovieGifAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg panel:       The :class:`.CanvasPanel` to generate the animated
                          GIF for.
        """

        base.Action.__init__(self, overlayList, displayCtx, self.__doMakeGif)

        self.__name  = '{}_{}'.format(type(self).__name__, id(self))
        self.__panel = panel

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        panel      .addListener('movieAxis',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``MovieGifAction`` is no longer neded.
        Removes some property listeners.
        """
        self.overlayList.removeListener('overlays',        self.__name)
        self.displayCtx .removeListener('selectedOverlay', self.__name)
        self.__panel    .removeListener('movieAxis',       self.__name)
        base.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Enables/disables this action based on whether a movie can be played
        (see :meth:`.CanvasPanel.canRunMovie`).
        """

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            self.enabled = False
            return

        opts = self.displayCtx.getOpts(overlay)

        self.enabled = self.__panel.canRunMovie(overlay, opts)


    def __doMakeGif(self):
        """Prompts the user to select a file to save the movie to, and then
        generates the movie via :func:`makeGif`.
        """

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
            if self.__progdlg is not None and isalive(self.__progdlg):
                self.__progdlg.DoBounce('Saved frame {}...'.format(frame))
                return not self.__progdlg.WasCancelled()
            else:
                return False

        def finish():
            if isalive(self.__progdlg):
                self.__progdlg.Hide()
                self.__progdlg.Close()
            self.__progdlg = None

        # TODO prompt user to select axis/delay/limits?
        self.__progdlg.Show()
        makeGif(self.overlayList,
                self.displayCtx,
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
    """Save an animated gif of the currently selected overlay, according to the
    current movie mode settings.

    .. note:: This function will return immediately, as the animated GIF is
              generated on the ``wx`` :mod:`.idle` loop.

    :arg overlayList: The :class:`.OverlayList`
    :arg displayCtx:  The :class:`.DisplayContext`
    :arg panel:       The :class:`.CanvasPanel`.
    :arg filename:    Name of file to save the movie to
    :arg progfunc:    Function which will be called after each frame is saved.
    :arg onfinish:    Function which will be called after all frames have been
                      saved.
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
    ctx     = MovieContext(is3d)

    class Finished(Exception):
        pass

    class Cancelled(Exception):
        pass

    def finalise(ctx):
        if not ctx.cancelled and len(ctx.images) > 0:
            ctx.images[0].save(filename,
                               format='gif',
                               save_all=True,
                               append_images=ctx.images[1:],
                               duration=50,
                               loop=0)
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
        """Capture one frame, update the view to the next frame, and
        schedule the next frame capture.
        """
        try:
            panel.movieSync()
            realCaptureFrame(ctx)
            idle.idleWhen(captureFrame, ready, ctx, after=0.1)
            panel.doMovieUpdate(overlay, opts)

        except Finished:
            finalise(ctx)

        except (Cancelled, Exception) as e:
            ctx.cancelled = True
            finalise(ctx)

    def realCaptureFrame(ctx):
        """Capture a movie frame. Raise Cancelled() if the user cancels,
        or Finished() when the movie capture is complete.
        """

        # individual frames don't
        # need to be saved as gif
        idx   = len(ctx.frames)
        fname = op.join(tempdir, '{}.png'.format(idx))
        frame = panel.getMovieFrame(overlay, opts)

        if not progfunc(idx):
            raise Cancelled()

        frame, finished = ctx.processFrame(frame)

        if finished:
            raise Finished()

        screenshot.screenshot(panel, fname)
        ctx.addFrame(frame, PIL.Image.open(fname))

    idle.idleWhen(captureFrame, ready, ctx, after=0.1)


class MovieContext:
    """Used by :func:`makeGif`. Stores references to captured frames,
    and contains logic to detect when enough frames have been captured.
    """

    def __init__(self, is3d):
        """Create a ``MovieContext``.

        If ``is3d is True``, it is assumed that we are capturing a movie
        from a :class:`.Scene3DPanel` along the X/Y/Z axes (i.e. the scene
        is rotating around).

        Otherwise is is assumed that we are capturing a movie through time,
        or along the X/Y/Z axes in 2D (i.e. scrolling through slices in
        an :class:`.OrthoView`).
        """
        self.is3d       = is3d
        self.looped     = False
        self.cancelled  = False
        self.startFrame = None
        self.images     = []
        self.frames     = []

    def addFrame(self, frame, image):
        """Save refs to a movie frame and associated screenshot. """
        self.images.append(image)
        self.frames.append(frame)

    def processFrame(self, frame):
        """Return true if the movie has completed. The provided ``frame``
        is the value of the next frame that would be captured.
        """
        # The 3D X/Y/Z movie mode performs rotations,
        # rather than moving the display location
        # through the X/Y/Z axes. The "frame" returned
        # by getMovieFrame is a rotation matrix.  We
        # convert these rotation matrices into
        # rms-deviations (average deviation of the
        # current frame from the starting frame), which
        # has an inverted "V"-shaped wave form as the
        # scene is rotated 360 degrees. So we continue
        # capturing frames until the rmsdev of the
        # current frame is:
        #
        #   - close to 0 (i.e. very similar to
        #     the rotation matrix of the starting
        #     frame), and
        #
        #   - less than the most recent frame (i.e.
        #     has rotated past 180 degrees, and is
        #     rotating back twoards the starting
        #     point)

        if self.is3d:

            # save a ref to the starting rotation matrix
            if len(self.frames) == 0:
                self.startFrame = frame

            # normalise the rotmat for this
            # frame to the rms difference
            # from the starting rotmat
            frame = affine.rmsdev(self.startFrame, frame)

            # Keep capturing frames until we
            # have performed a full 360 degree
            # rotation (rmsdev of current
            # frame is decreasing towards 0)
            if len(self.frames) > 1    and \
               frame < self.frames[-1] and \
               abs(frame) < 0.1:
                return frame, True

        # All other movie frames have a range
        # (fmin, fmax) and start at some arbitrary
        # point within this range. We capture frames
        # until a full loop through this range has
        # been completed.
        else:
            # detect when frame has wrapped around
            # back to the beginning of the range
            if not self.looped:
                self.looped = (len(self.frames) > 1) and \
                              (frame <= self.frames[-1])

            if self.looped and frame >= self.frames[0]:
                return frame, True

        return frame, False
