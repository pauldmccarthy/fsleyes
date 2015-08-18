#!/usr/bin/env python
#
# saveoverlay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import fsl.data.image      as fslimage
import fsl.fsleyes.actions as actions


log = logging.getLogger(__name__)


class SaveOverlayAction(actions.Action):

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
        
        overlay = self._displayCtx.getSelectedOverlay()

        # TODO  Support for other overlay types

        self.enabled = ((overlay is not None)               and
                        isinstance(overlay, fslimage.Image) and 
                        (not overlay.saved))

        for ovl in self._overlayList:
            if not isinstance(ovl, fslimage.Image):
                continue
            
            ovl.removeListener('saved', self._name)
            
            if ovl is overlay:
                ovl.addListener('saved',
                                self._name,
                                self.__overlaySaveStateChanged)
 

    def __overlaySaveStateChanged(self, *a):
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if overlay is None:
            self.enabled = False
            
        elif not isinstance(overlay, fslimage.Image):
            self.enabled = False
        else:
            self.enabled = not overlay.saved

        
    def doAction(self):
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if overlay is None:
            return

        # TODO support for other overlay types
        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('Non-volumetric types not supported yet') 
        
        overlay.save()
