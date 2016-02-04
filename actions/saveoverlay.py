#!/usr/bin/env python
#
# saveoverlay.py - Save the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveOverlayAction`, which allows the user
to save the currently selected overlay.
"""


import fsl.data.image as fslimage
import                   action


class SaveOverlayAction(action.Action):
    """The ``SaveOverlayAction`` allows the user to save the currently
    selected overlay, if it has been edited, or only exists in memory.
    """

    
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``SaveOverlayAction``. 
        
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """
        action.Action.__init__(self, self.__saveOverlay)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """

        self.__displayCtx .removeListener('selectedOverlay', self.__name)
        self.__overlayList.removeListener('overlays',        self.__name)
        action.Action.destroy(self)

        
    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list changes.

        If the overlay is a :class:`.Image`, and it has unsaved changes,
        this action is enabled; otherwise it is disabled.
        """
        
        overlay = self.__displayCtx.getSelectedOverlay()

        # TODO  Support for other overlay types

        self.enabled = ((overlay is not None)               and
                        isinstance(overlay, fslimage.Image) and 
                        (not overlay.saved))

        for ovl in self.__overlayList:
            if not isinstance(ovl, fslimage.Image):
                continue
            
            ovl.removeListener('saved', self.__name)

            # Register a listener on the saved property
            # of the currently selected image, so we can
            # enable the save action when the image
            # becomes 'unsaved', and vice versa.
            if ovl is overlay:
                ovl.addListener('saved',
                                self.__name,
                                self.__overlaySaveStateChanged)
 

    def __overlaySaveStateChanged(self, *a):
        """Called when the :attr:`.Image.saved` property of the currently
        selected overlay changes. Enables/disables this ``SaveOverlayAction``
        accordingly.

        This is only applicable if the current overlay is a :class:`.Image` -
        see the :meth:`__selectedOverlayChanged` method.
        """
        
        overlay = self.__displayCtx.getSelectedOverlay()
        
        if overlay is None:
            self.enabled = False
            
        elif not isinstance(overlay, fslimage.Image):
            self.enabled = False
        else:
            self.enabled = not overlay.saved

        
    def __saveOverlay(self):
        """Saves the currently selected overlay (only if it is a
        :class:`.Image`), by a call to :meth:`.Image.save`.
        """
        
        overlay = self.__displayCtx.getSelectedOverlay()
        
        if overlay is None:
            return

        # TODO support for other overlay types
        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('Non-volumetric types not supported yet') 
        
        overlay.save()
