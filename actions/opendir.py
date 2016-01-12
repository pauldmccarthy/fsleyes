#!/usr/bin/env python
#
# opendir.py - Action which allows the user to load overlays specified with a
#              directory.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OpenDirAction`, which allows the user to
load overlay files, specified with a directory, into the :class:`.OverlayList`.
"""


import action

import fsl.fsleyes.autodisplay as autodisplay


class OpenDirAction(action.Action):
    """The ``OpenDirAction`` allows the user to add overlays to the
    :class:`.OverlayList`. This functionality is provided by the
    :meth:`.OverlayList.addOverlays` method.
    """

    def __init__(self, overlayList, displayCtx):
        """Create an ``OpenDirAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        action.Action.__init__(self, self.__openDir)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        

    def __openDir(self):
        """Calls :meth:`.OverlayList.addOverlays` method. If overlays were added,
        updates the :attr:`.DisplayContext.selectedOverlay` accordingly.
        """

        def onLoad(overlays):

            if len(overlays) == 0:
                return
        
            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]

            if self.__displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)
                    
        self.__overlayList.addOverlays(dirdlg=True, onLoad=onLoad)
