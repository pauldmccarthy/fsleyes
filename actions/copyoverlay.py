#!/usr/bin/env python
#
# copyoverlay.py - Action which copies the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CopyOverlayAction`, a global action
which creates a copy of the currently selected overlay.
"""


import numpy          as np

import                   action
import fsl.data.image as fslimage


class CopyOverlayAction(action.Action):
    """The ``CopyOverlayAction`` does as its name suggests - it creates a
    copy of the currently selected overlay.
    """

    
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``CopyOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """
        action.Action.__init__(self, self.__copyOverlay)

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
        """Called when the selected overlay, or overlay list, changes.
        
        Enables/disables this action depending on the nature of the selected
        overlay.
        """
        
        ovl          = self.__displayCtx.getSelectedOverlay()
        self.enabled = (ovl is not None) and (type(ovl) == fslimage.Image)
    
    
    def __copyOverlay(self):
        """Creates a copy of the currently selected overlay, and inserts it
        into the :class:`.OverlayList`.
        """

        ovlIdx  = self.__displayCtx.selectedOverlay
        overlay = self.__overlayList[ovlIdx]

        if overlay is None:
            return

        # TODO support for other overlay types
        if type(overlay) != fslimage.Image:
            raise RuntimeError('Currently, only {} instances can be '
                               'copied'.format(fslimage.Image.__name__))
                
        data   = np.copy(overlay.data)
        header = overlay.nibImage.get_header()
        name   = '{}_copy'.format(overlay.name)
        copy   = fslimage.Image(data, name=name, header=header)
        
        self.__overlayList.insert(ovlIdx + 1, copy)
        
        # Copy the Display settings
        srcDisplay  = self.__displayCtx.getDisplay(overlay)
        destDisplay = self.__displayCtx.getDisplay(copy)

        for prop in srcDisplay.getAllProperties()[0]:
            
            # Don't override the name
            # that we set above
            if prop == 'name':
                continue
            
            val = getattr(srcDisplay, prop)
            setattr(destDisplay, prop, val)

        # And after the Display has been configured
        # copy the DisplayOpts settings.
        srcOpts  = self.__displayCtx.getOpts(overlay)
        destOpts = self.__displayCtx.getOpts(copy)

        for prop in srcOpts.getAllProperties()[0]:
            val = getattr(srcOpts, prop)
            setattr(destOpts, prop, val)
