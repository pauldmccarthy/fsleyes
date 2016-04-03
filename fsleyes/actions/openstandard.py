#!/usr/bin/env python
#
# openstandard.py - Action which allows the user to open standard images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OpenStandardAction`, which allows the user
to load in standard space images from the ``$FSLDIR/data/standard/`` directory.
"""


import os.path as op

from . import action

import fsl.utils.platform as fslplatform


class OpenStandardAction(action.Action):
    """The ``OpenStandardAction`` prompts the user to open one or more
    overlays, using ``$FSLDIR/data/standard/`` as the default directory.
    """

    
    def __init__(self, overlayList, displayCtx, frame):
        """Create an ``OpenStandardAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """ 
        action.Action.__init__(self, self.__openStandard)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        
        self.__setStandardDir()

        # If FSLDIR is not set, the setStandardDir
        # disables this action. But we'll listen 
        # for changes to FSLDIR, in case it gets 
        # set later on.
        fslplatform.platform.register(
            '{}_{}'.format(type(self).__name__, id(self)),
            self.__setStandardDir)

        
    def destroy(self):
        """Must be called when this ``OpenStandardAction`` is no longer
        needed. Performs some clean-up.
        """
        fslplatform.platform.deregister(
            '{}_{}'.format(type(self).__name__, id(self)))


    def __setStandardDir(self, *a):
        """Called by :meth:`__init__`, and when the
        :attr:`~fsl.utils.Platform.fsldir` property is changed. Updates
        the path to the FSLDIR standard directory.
        """

        fsldir = fslplatform.platform.fsldir
        
        if fsldir is not None:
            self.__stddir = op.join(fsldir, 'data', 'standard')
        else:
            self.__stddir = None
            
        self.enabled = self.__stddir is not None
            
        
    def __openStandard(self):
        """Calls the :meth:`.OverlayList.addOverlays` method. If the user
        added some overlays, updates the
        :attr:`.DisplayContext.selectedOverlay` accordingly.
        """

        def onLoad(overlays):
        
            if len(overlays) > 0:
                self.__displayCtx.selectedOverlay = \
                    self.__displayCtx.overlayOrder[0]
        
        self.__overlayList.addOverlays(
            fromDir=self.__stddir, addToEnd=False, onLoad=onLoad)
