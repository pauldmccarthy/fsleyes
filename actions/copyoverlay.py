#!/usr/bin/env python
#
# copyoverlay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy               as np

import fsl.fsleyes.actions as actions
import fsl.data.image      as fslimage


class CopyOverlayAction(actions.Action):

    def __init__(self, *args, **kwargs):
        actions.Action.__init__(self, *args, **kwargs)

        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()

        
    def __selectedOverlayChanged(self, *a):
        self.enabled = self._displayCtx.getSelectedOverlay() is not None
    
    
    def doAction(self):

        ovlIdx  = self._displayCtx.selectedOverlay
        overlay = self._overlayList[ovlIdx]

        if overlay is None:
            return

        # TODO support for other overlay types
        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('Currently, only {} instances can be '
                               'copied'.format(fslimage.Image.__name__))
                
        data   = np.copy(overlay.data)
        header = overlay.nibImage.get_header()
        name   = '{}_copy'.format(overlay.name)
        copy   = fslimage.Image(data, name=name, header=header)

        # TODO copy display properties
        
        self._overlayList.insert(ovlIdx + 1, copy)
