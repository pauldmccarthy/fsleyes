#!/usr/bin/env python
#
# saveoverlay.py - Save the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveOverlayAction`, which allows the user
to save the currently selected overlay.
"""


import logging

import fsl.data.image      as fslimage
import fsl.fsleyes.actions as actions


log = logging.getLogger(__name__)


class SaveOverlayAction(actions.Action):
    """The ``SaveOverlayAction`` allows the user to save the currently
    selected overlay, if it has been edited, or only exists in memory.
    """

    
    def __init__(self, *args, **kwargs):
        """Create a ``SaveOverlayAction``. All arguments are passed through
        to the :meth:`.Action.__init__` constructor.
        """
        actions.Action.__init__(self, *args, **kwargs)        

        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        actions.Action.destroy(self)

        
    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list changes.

        If the overlay is a :class:`.Image`, and it has unsaved changes,
        this action is enabled; otherwise it is disabled.
        """
        
        overlay = self._displayCtx.getSelectedOverlay()

        # TODO  Support for other overlay types

        self.enabled = ((overlay is not None)               and
                        isinstance(overlay, fslimage.Image) and 
                        (not overlay.saved))

        for ovl in self._overlayList:
            if not isinstance(ovl, fslimage.Image):
                continue
            
            ovl.removeListener('saved', self._name)

            # Register a listener on the saved property
            # of the currently selected image, so we can
            # enable the save action when the image
            # becomes 'unsaved', and vice versa.
            if ovl is overlay:
                ovl.addListener('saved',
                                self._name,
                                self.__overlaySaveStateChanged)
 

    def __overlaySaveStateChanged(self, *a):
        """Called when the :attr:`.Image.saved` property of the currently
        selected overlay changes. Enables/disables this ``SaveOverlayAction``
        accordingly.

        This is only applicable if the current overlay is a :class:`.Image` -
        see the :meth:`__selectedOverlayChanged` method.
        """
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if overlay is None:
            self.enabled = False
            
        elif not isinstance(overlay, fslimage.Image):
            self.enabled = False
        else:
            self.enabled = not overlay.saved

        
    def doAction(self):
        """Saves the currently selected overlay (only if it is a
        :class:`.Image`), by a call to :meth:`.Image.save`.
        """
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if overlay is None:
            return

        # TODO support for other overlay types
        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('Non-volumetric types not supported yet') 
        
        overlay.save()
