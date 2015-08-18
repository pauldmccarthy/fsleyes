#!/usr/bin/env python
#
# openfileaction.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op

import logging
log = logging.getLogger(__name__)

import fsl.fsleyes.actions as actions

class OpenStandardAction(actions.Action):
    def __init__(self, overlayList, displayCtx):
        actions.Action.__init__(self, overlayList, displayCtx)
        
        # disable the 'add standard' menu
        # item if $FSLDIR is not set
        fsldir = os.environ.get('FSLDIR', None)

        if fsldir is not None:
            self._stddir = op.join(fsldir, 'data', 'standard')
        else:
            self._stddir = None
            self.enabled = False
        
        
    def doAction(self):
        if self._overlayList.addOverlays(self._stddir, addToEnd=False):
            self._displayCtx.selectedOverlay = self._displayCtx.overlayOrder[0]
