#!/usr/bin/env python
#
# copyoverlay.py - Action which copies the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CopyOverlayAction`, a global action
which creates a copy of the currently selected overlay.
"""

import logging

import numpy               as np

import fsl.fsleyes.actions as actions
import fsl.data.image      as fslimage


log = logging.getLogger(__name__)


class CopyOverlayAction(actions.Action):
    """The ``CopyOverlayAction`` does as its name suggests - it creates a
    copy of the currently selected overlay.
    """

    
    def __init__(self, overlayList, displayCtx):
        """Create a ``CopyOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        actions.Action.__init__(self, self.__copyOverlay)

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
        actions.Action.destroy(self)

        
    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list, changes.
        
        Enables/disables this action depending on the nature of the selected
        overlay.
        """
        overlay = self.__displayCtx.getSelectedOverlay()
        
        self.enabled = (overlay is not None) and \
                       isinstance(overlay, fslimage.Image)
    
    
    def __copyOverlay(self):
        """Creates a copy of the currently selected overlay, and inserts it
        into the :class:`.OverlayList`.
        """

        ovlIdx  = self.__displayCtx.selectedOverlay
        overlay = self.__overlayList[ovlIdx]

        if overlay is None:
            return

        # TODO support for other overlay types
        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('Currently, only {} instances can be '
                               'copied'.format(fslimage.Image.__name__))
                
        data   = np.copy(overlay.data)
        header = overlay.nibImage.get_header()
        name   = '{}_copy'.format(overlay.name)
        copy   = fslimage.Image(data, name=name, header=header)

        # TODO copy display properties
        
        self.__overlayList.insert(ovlIdx + 1, copy)
