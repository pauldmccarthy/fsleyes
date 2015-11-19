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

import action


class OpenStandardAction(action.Action):
    """The ``OpenStandardAction`` prompts the user to open one or more
    overlays, using ``$FSLDIR/data/standard/`` as the default directory.
    """

    
    def __init__(self, overlayList, displayCtx):
        """Create an ``OpenStandardAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """ 
        action.Action.__init__(self, self.__openStandard)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        
        # disable this action
        # if $FSLDIR is not set
        fsldir = os.environ.get('FSLDIR', None)

        if fsldir is not None:
            self.__stddir = op.join(fsldir, 'data', 'standard')
        else:
            self.__stddir = None
            self.enabled  = False
        
        
    def __openStandard(self):
        """Calls the :meth:`.OverlayList.addOverlays` method. If the user
        added some overlays, updates the
        :attr:`.DisplayContext.selectedOverlay` accordingly.
        """
        if self.__overlayList.addOverlays(self.__stddir, addToEnd=False):
            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[0]
