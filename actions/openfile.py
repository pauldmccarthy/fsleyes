#!/usr/bin/env python
#
# openfileaction.py - Action which allows the user to load overlay files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OpenFileAction`, which allows the user to
load overlay files into the :class:`.OverlayList`.
"""


import logging

import fsl.fsleyes.actions as actions


log = logging.getLogger(__name__)


class OpenFileAction(actions.Action):
    """The ``OpenFileAction`` allows the user to add files to the
    :class:`.OverlayList`. This functionality is provided by the
    :meth:`.OverlayList.addOverlays` method.
    """

    def __init__(self, overlayList, displayCtx):
        """Create an ``OpenFileAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        actions.Action.__init__(self, self.__openFile)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        

    def __openFile(self):
        """Calls :meth:`.OverlayList.addOverlays` method. If overlays were added,
        updates the :attr:`.DisplayContext.selectedOverlay` accordingly.
        """
        
        if self.__overlayList.addOverlays():
            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]
