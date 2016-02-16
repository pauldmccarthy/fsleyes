#!/usr/bin/env python
#
# removeoverlay.py - Action which removes the current overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RemoveOverlayAction`, which allows the uesr
to remove the currently selected overlay.
"""


import action


class RemoveOverlayAction(action.Action):
    """The ``RemoveOverlayAction`` allows the uesr to remove the currently
    selected overlay.
    """

    
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``RemoveOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """ 

        action.Action.__init__(self, self.__removeOverlay)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)

        
    def destroy(self):
        """Must be called when this ``RemoveOverlayAction`` is no longer
        needed. Removes property listeners, and then calls
        :meth:`.Action.destroy`.
        """
        self.__overlayList.removeListener('overlays', self.__name)
        action.Action.destroy(self)

        
    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Updates the
        :attr:`.Action.enabled` flag
        """
        self.enabled = len(self.__overlayList) > 0

        
    def __removeOverlay(self):
        """Removes the currently selected overlay (as defined by the
        :attr:`.DisplayContext.selectedOverlay) from the :class:`.OverlayList`.
        """
        if len(self.__overlayList) > 0:
            self.__overlayList.pop(self.__displayCtx.selectedOverlay)
