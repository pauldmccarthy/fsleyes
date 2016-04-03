#!/usr/bin/env python
#
# openfile.py - Action which allows the user to load overlay files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OpenFileAction`, which allows the user to
load overlay files into the :class:`.OverlayList`.
"""


import action

import fsl.fsleyes.autodisplay as autodisplay


class OpenFileAction(action.Action):
    """The ``OpenFileAction`` allows the user to add files to the
    :class:`.OverlayList`. This functionality is provided by the
    :meth:`.OverlayList.addOverlays` method.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create an ``OpenFileAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """
        action.Action.__init__(self, self.__openFile)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        

    def __openFile(self):
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
        
        self.__overlayList.addOverlays(onLoad=onLoad)
