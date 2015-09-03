#!/usr/bin/env python
#
# openstandardaction.py - Action which allows the user to open standard
#                         images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OpenStandardAction`, which allows the user
to load in standard space images from the ``$FSLDIR/data/standard/`` directory.
"""


import os
import os.path as op

import logging

import fsl.fsleyes.actions as actions


log = logging.getLogger(__name__)


class OpenStandardAction(actions.Action):
    """The ``OpenStandardAction`` prompts the user to open one or more
    overlays, using ``$FSLDIR/data/standard/`` as the default directory.
    """
    def __init__(self, overlayList, displayCtx):
        actions.Action.__init__(self, overlayList, displayCtx)
        
        # disable this action
        # if $FSLDIR is not set
        fsldir = os.environ.get('FSLDIR', None)

        if fsldir is not None:
            self.__stddir = op.join(fsldir, 'data', 'standard')
        else:
            self.__stddir = None
            self.enabled  = False
        
        
    def doAction(self):
        """Calls the :meth:`.OverlayList.addOverlays` method. If the user
        added some overlays, updates the
        :attr:`.DisplayContext.selectedOverlay` accordingly.
        """
        if self._overlayList.addOverlays(self.__stddir, addToEnd=False):
            self._displayCtx.selectedOverlay = self._displayCtx.overlayOrder[0]
