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
    copy  of the currently selected overlay.
    """

    
    def __init__(self, *args, **kwargs):
        """Create a ``CopyOverlayAction``. All arguments are passed through
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

        
    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list, changes.
        
        Enables/disables this action depending on the nature of the selected
        overlay.
        """
        overlay = self._displayCtx.getSelectedOverlay()
        
        self.enabled = (overlay is not None) and \
                       isinstance(overlay, fslimage.Image)


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        actions.Action.destroy(self)
    
    
    def doAction(self):
        """Creates a copy of the currently selected overlay, and inserts it
        into the :class:`.OverlayList`.
        """

        ovlIdx  = self._displayCtx.selectedOverlay
        overlay = self._overlayList[ovlIdx]

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
        
        self._overlayList.insert(ovlIdx + 1, copy)
