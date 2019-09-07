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
        base.Action.__init__(self, overlayList, displayCtx, self.__openDir)


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

            self.overlayList.extend(overlays)
            self.displayCtx.selectedOverlay = self.displayCtx.overlayOrder[-1]

            if self.displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.overlayList,
                                            self.displayCtx)

        loadoverlay.interactiveLoadOverlays(
            dirdlg=True,
            onLoad=onLoad,
            inmem=self.displayCtx.loadInMemory)
