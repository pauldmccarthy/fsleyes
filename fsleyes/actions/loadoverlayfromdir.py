#!/usr/bin/env python
#
# loadoverlayfromdir.py - Action which allows the user to load overlays
#                         specified with a directory.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadOverlayFromDirAction`, which allows
the user to load overlay files, specified with a directory, into the
:class:`.OverlayList`.
"""


import fsleyes.autodisplay as autodisplay
from . import                 loadoverlay
from . import                 base


class LoadOverlayFromDirAction(base.Action):
    """The ``LoadOverlayFromDirAction`` allows the user to add overlays
    to the :class:`.OverlayList`. This functionality is provided by functions
    in the :mod:`.loadoverlay` module.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create an ``OpenDirAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__openDir)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __openDir(self):
        """Calls the :func:`.loadoverlay.interactiveLoadOverlays` method.

        If overlays were added, updates the
        :attr:`.DisplayContext.selectedOverlay` accordingly.

        If :attr:`.DisplayContext.autoDisplay` is ``True``, uses the
        :mod:`.autodisplay` module to configure the display properties
        of each new overlay.
        """

        def onLoad(paths, overlays):

            if len(overlays) == 0:
                return

            self.__overlayList.extend(overlays)

            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]

            if self.__displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)

        loadoverlay.interactiveLoadOverlays(
            dirdlg=True,
            onLoad=onLoad,
            inmem=self.__displayCtx.loadInMemory)
