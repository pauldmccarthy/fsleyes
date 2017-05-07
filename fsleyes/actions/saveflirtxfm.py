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
import fsl.utils.transform          as transform
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
from . import                          base
from . import                          applyflirtxfm


log = logging.getLogger(__name__)


class SaveFlirtXfmAction(base.Action):
    """The :class:`SaveFlirtXfmAction` class is an :class:`.Action` which
    allows the user to save an :class:`.Image` transformation to disk for
    use with FLIRT.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``SaveFlirtXfmAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__saveFlirtXfm)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)


    def destroy(self):
        """Must be called when this ``SaveFlirtXfmAction`` is no longer needed.
        """
        self.__overlayList.removeListener('overlays')
        self.__displayCtx .removeListener('selectedOverlay')
        self.__overlayList = None
        self.__displayCtx  = None
        self.__frame       = None

        base.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Updates the :attr:`.Action.enabled` state of this action.
        """

        overlay      = self.__displayCtx.getSelectedOverlay()
        self.enabled = isinstance(overlay, fslimage.Image)


    def __saveFlirtXfm(self):
        """Called when this action is executed. Prompts the user to save
        a FLIRT transform for the currently selected image.
        """

        displayCtx  = self.__displayCtx
        overlayList = self.__overlayList
        overlay     = displayCtx.getSelectedOverlay()

        matFile, refFile = applyflirtxfm.promptForFlirtFiles(
            self.__frame, overlay, overlayList, displayCtx, save=True)

        if matFile is None or refFile is None:
            return

        xform = calculateTransform(
            overlay, overlayList, displayCtx, refFile)

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

    return transform.sformToFlirtMatrix(overlay, refImg, srcXform)
