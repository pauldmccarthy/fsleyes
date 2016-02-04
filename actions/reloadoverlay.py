#!/usr/bin/env python
#
# reloadoverlay.py - The ReloadOverlayAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ReloadOverlayAction`, a global action
which reloads the currently selected overlay from disk.
"""


import logging

import action

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


class ReloadOverlayAction(action.Action):
    """The ``ReloadOverlayAction`` reloads the currently selected overlay
    from disk. Currently only :class:`.Image` overlays are supported.
    """
    
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``ReloadOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """ 
        action.Action.__init__(self, self.__reloadOverlay)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()

        
    def destroy(self):
        """Must be called when this ``ReloadOverlayAction`` is no longer
        required. Removes some property listeners, and calls
        :meth:`.Action.destroy`.
        """
        self.__overlayList.removeListener('overlays',        self.__name)
        self.__displayCtx .removeListener('selectedOverlay', self.__name)

        action.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the currently selected overlay changes. Enables/disables
        this ``Action`` depending on the type of the newly selected overlay.
        """

        # This action is permanently disabled until
        # I write the __reloadOverlay method.
        self.enabled = False

        if True:
            return

        ovl          = self.__displayCtx.getSelectedOverlay()
        self.enabled = (ovl is not None) and (type(ovl) == fslimage.Image)

    
    def __reloadOverlay(self):
        """Reloads the currently selected overlay from disk.
        """
        ovl = self.__displayCtx.getSelectedOverlay()

        if ovl is None or type(ovl) != fslimage.Image:
            raise RuntimeError('Only Image overlays can be reloaded')

        # 1. Get references to all Display/DisplayOpts
        #    instances, and save all their settings.

        # 2. Get the overlay data source

        # 3. Remove the overlay from the overlay list
 
        # 4. Re-add the overlay at the same
        #    location in the overlay list

        # 5. Re-configure the new Display/DisplayOpts
        #    instances settings saved in step 1.

        log.warn('Not functional yet')
