#!/usr/bin/env python
#
# moviegif.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            shutil
import            tempfile

import PIL

import fsl.utils.transform as transform

from . import base

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

        base.Action.__init__(self, self.__doGif)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__panel       = panel


    def __doGif(self):

        # TODO prompt user to select file
        # TODO prompt user to select axis/delay/limits?

        makeGif(self.__displayCtx, self.__panel, 'movie.gif')


def makeGif(displayCtx, panel, filename):
    """bah, humbug
    """

    overlay = displayCtx.getSelectedOverlay()
    opts    = displayCtx.getOpts(overlay)
    images  = []
    tempdir = tempfile.mkdtemp()

    idx     = 0
    start   = None
    last    = None
    cur     = None
    looped  = False

    is3d = isinstance(panel, scene3dpanel.Scene3DPanel) and \
           panel.movieAxis != 3

    try:

        while True:

            fname = op.join(tempdir, '{}.gif'.format(idx))
            idx  += 1

            screenshot.screenshot(panel, fname)
            images.append(PIL.Image.open(fname))

            cur = panel.doMovieUpdate(overlay, opts)

            if start is None:
                start = cur

            print('start: {}, cur: {}'.format(start, cur))

            if is3d:


                pass

            else:
                if not looped and last is not None and cur < last:
                    looped = True

                if looped and cur > start:
                    break

            last = cur

        images[0].save(filename,
                       format='gif',
                       save_all=True,
                       append_images=images[1:])

    finally:
        shutil.rmtree(tempdir)




def rmsdev(T1, T2, R=None, xc=None):

    if R is None:
        R = 1

    if xc is None:
        xc = np.zeros(3)

    # rotations only
    if T1.shape == (3, 3):
        M = np.dot(T2, invert(T1)) - np.eye(3)
        A = M[:3, :3]
        t = np.zeros(3)

    # full affine
    else:
        M = np.dot(T2, invert(T1)) - np.eye(4)
        A = M[:3, :3]
        t = M[:3,  3]

    Axc = np.dot(A, xc)

    erms = np.dot((t + Axc).T, t + Axc)
    erms = 0.2 * R ** 2 * np.dot(A.T, A).trace() + erms
    erms = np.sqrt(erms)

    return erms
