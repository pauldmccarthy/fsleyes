#!/usr/bin/env python
#
# openfileaction.py - Action which allows the user to load overlay files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OpenFileAction`, which allows the user to
load overlay files into the :class:`.OverlayList`.
"""


import action

import fsl.fsleyes.displaydefaults as displaydefaults


class OpenFileAction(action.Action):
    """The ``OpenFileAction`` allows the user to add files to the
    :class:`.OverlayList`. This functionality is provided by the
    :meth:`.OverlayList.addOverlays` method.
    """

    def __init__(self, overlayList, displayCtx):
        """Create an ``OpenFileAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        action.Action.__init__(self, self.__openFile)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        

    def __openFile(self):
        """Calls :meth:`.OverlayList.addOverlays` method. If overlays were added,
        updates the :attr:`.DisplayContext.selectedOverlay` accordingly.
        """

        overlays = self.__overlayList.addOverlays()

        if len(overlays) == 0:
            return
        
        self.__displayCtx.selectedOverlay = self.__displayCtx.overlayOrder[-1]

        for overlay in overlays:
            displaydefaults.displayDefaults(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)
