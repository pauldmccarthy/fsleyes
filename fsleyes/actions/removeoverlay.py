#!/usr/bin/env python
#
# removeoverlay.py - Action which removes the current overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RemoveOverlayAction` class, and the
:func:`removeOverlay` function, which provides logic to remove an overlay
from the :class:`.OverlayList`.
"""


import fsl.data.image  as fslimage
import fsleyes.strings as strings
from . import             base


class RemoveOverlayAction(base.Action):
    """The ``RemoveOverlayAction`` allows the uesr to remove the currently
    selected overlay.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``RemoveOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        base.Action.__init__(self, self.__removeOverlay)

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
        base.Action.destroy(self)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Updates the
        :attr:`.Action.enabled` flag
        """
        self.enabled = len(self.__overlayList) > 0


    def __removeOverlay(self):
        """Removes the currently selected overlay (as defined by the
        :attr:`.DisplayContext.selectedOverlay) from the :class:`.OverlayList`.
        """
        removeOverlay(self.__overlayList, self.__displayCtx)


def removeOverlay(overlayList, displayCtx, overlay=None, stringKey=None):
    """Removes the specified overlay (or the currently selected overlay,
    if ``overlay is None``) from the overlay list. If the overlay is not
    saved, the user is prompted to confirm the removal.

    :arg overlay:   Overlay to remove. If ``None``, the currently selected
                    overlay is removed.

    :arg stringKey: Key to use in the :mod:`.strings` module for the
                    dialog with which the user is prompted if the overlay
                    has unsaved changes.

    :returns:       ``True`` if the overlay was removed, ``False`` otherise.
    """

    import wx

    if overlay is None:
        overlay = displayCtx.getSelectedOverlay()

    if stringKey is None:
        stringKey = 'removeoverlay.unsaved'

    if isinstance(overlay, fslimage.Image) and not overlay.saveState:

        msg    = strings.messages[stringKey]
        title  = strings.titles[  stringKey]
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
            return False

    overlayList.remove(overlay)
    return True
