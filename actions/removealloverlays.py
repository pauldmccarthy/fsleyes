#!/usr/bin/env python
#
# removealloverlays.py - The RemoveAllOverlaysAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RemoveAllOverlaysAction`, which allows the
uesr to remove all overlays from the :class:`.OverlayList`.
"""


import action


class RemoveAllOverlaysAction(action.Action):
    """The ``RemoveAllOverlaysAction`` allows the uesr to remove all
    overlays from the :class:`.OverlayList`.
    """

    def __init__(self, overlayList, displayCtx):
        """Create a ``RemoveAllOverlaysAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """ 

        action.Action.__init__(self, self.__removeOverlay)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)

        
    def destroy(self):
        """Must be called when this ``RemoveAllOverlaysAction`` is no longer
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
        """Removes all overlays from the :class:`.OverlayList`.
        """
        del self.__overlayList[:]
