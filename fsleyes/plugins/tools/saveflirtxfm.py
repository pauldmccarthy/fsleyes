#!/usr/bin/env python
#
# saveflirtxfm.py - The SaveFlirtXfmAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveFlirtXfmAction` class, an
:class:`.Action` which allows the user to save an :class:`.Image`
transformation to disk for use with FLIRT.
"""


import logging

import numpy as np

import fsl.data.image               as fslimage
import fsl.transform.affine         as affine
import fsl.transform.flirt          as flirt
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
import fsleyes.actions.base         as base
from . import                          applyflirtxfm


log = logging.getLogger(__name__)


class SaveFlirtXfmAction(base.NeedOverlayAction):
    """The :class:`SaveFlirtXfmAction` class is an :class:`.Action` which
    allows the user to save an :class:`.Image` transformation to disk, either
    as a FLIRT matrix, or a voxel-to-world matrix.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``SaveFlirtXfmAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.NeedOverlayAction.__init__(
            self, overlayList, displayCtx, func=self.__saveFlirtXfm)
        self.__frame = frame


    def destroy(self):
        """Must be called when this ``SaveFlirtXfmAction`` is no longer needed.
        """
        self.__frame = None
        base.NeedOverlayAction.destroy(self)


    def __saveFlirtXfm(self):
        """Called when this action is executed. Prompts the user to save
        a FLIRT transform for the currently selected image.
        """

        displayCtx  = self.displayCtx
        overlayList = self.overlayList
        overlay     = displayCtx.getSelectedOverlay()

        affType, matFile, refFile = applyflirtxfm.promptForFlirtFiles(
            self.__frame, overlay, overlayList, displayCtx, save=True)

        if all((affType is None, matFile is None, refFile is None)):
            return

        if affType == 'flirt':
            xform = calculateTransform(
                overlay, overlayList, displayCtx, refFile)
        else:
            xform = overlay.voxToWorldMat

        errtitle = strings.titles[  self, 'error']
        errmsg   = strings.messages[self, 'error']

        with status.reportIfError(errtitle, errmsg):
            np.savetxt(matFile, xform, fmt='%0.10f')


def calculateTransform(overlay,
                       overlayList,
                       displayCtx,
                       refFile,
                       srcXform=None):
    """Calculates and returns FLIRT transformation from the given ``overlay``
    to the image specified by the given ``refFile``.
    """

    # The reference image might
    # already be in the overlay list.
    refImg = overlayList.find(refFile)

    if refImg is None:
        refImg = fslimage.Image(refFile, loadData=False)

    return flirt.sformToFlirtMatrix(overlay, refImg, srcXform)
