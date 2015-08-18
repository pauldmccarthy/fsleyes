#!/usr/bin/env python
#
# openfileaction.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import fsl.fsleyes.actions as actions

class OpenFileAction(actions.Action):
    def doAction(self):
        
        if self._overlayList.addOverlays():
            self._displayCtx.selectedOverlay = \
                self._displayCtx.overlayOrder[-1]
