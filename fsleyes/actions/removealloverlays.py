#!/usr/bin/env python
#
# removealloverlays.py - The RemoveAllOverlaysAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RemoveAllOverlaysAction`, which allows the
uesr to remove all overlays from the :class:`.OverlayList`.
"""


import fsleyes.strings as strings
from . import             base
from . import             saveoverlay


class RemoveAllOverlaysAction(base.Action):
    """The ``RemoveAllOverlaysAction`` allows the uesr to remove all
    overlays from the :class:`.OverlayList`.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``RemoveAllOverlaysAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        base.Action.__init__(self, self.__removeAllOverlays)

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
        base.Action.destroy(self)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Updates the
        :attr:`.Action.enabled` flag
        """
        self.enabled = len(self.__overlayList) > 0


    def __removeAllOverlays(self):
        """Removes all overlays from the :class:`.OverlayList`.
        """

        import wx

        allSaved = saveoverlay.checkOverlaySaveState(
            self.__overlayList, self.__displayCtx)

        # If there are unsaved images,
        # get the user to confirm
        if not allSaved:

            msg    = strings.messages[self, 'unsavedOverlays']
            title  = strings.titles[  self, 'unsavedOverlays']
            parent = wx.GetApp().GetTopWindow()

            dlg = wx.MessageDialog(parent,
                                   message=msg,
                                   caption=title,
                                   style=(wx.YES_NO        |
                                          wx.NO_DEFAULT    |
                                          wx.CENTRE        |
                                          wx.ICON_WARNING))

            dlg.CentreOnParent()
            if dlg.ShowModal() == wx.ID_NO:
                return

        del self.__overlayList[:]
