#!/usr/bin/env python
#
# copyoverlay.py - Action which copies the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CopyOverlayAction`, a global action
which creates a copy of the currently selected overlay.
"""


import numpy              as np

import fsl.data.image     as fslimage
import fsl.utils.dialog   as fsldlg
import fsl.utils.settings as fslsettings
import fsleyes.strings    as strings
from . import                action


class CopyOverlayAction(action.Action):
    """The ``CopyOverlayAction`` does as its name suggests - it creates a
    copy of the currently selected overlay.


    .. note:: Currently this action is only capable of copying ``.Image``
              overlays.


    The user is asked to choose between the following options:

     - If the overlay is a 4D ``Image``, should we copy the entire 4D image,
       or extract the current 3D volume?
    
     - Should we copy all of the ``Image`` data, or create a blank
       (i.e. filled with zeros) ``Image`` of the same dimensions?

     - Should we copy the ``Image`` display properties
       (e.g. :attr:`.Display.overlayType`), or set the display properties
       of the copy to defaults?
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
        self.__frame       = frame
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
        
        import wx

        ovlIdx  = self.__displayCtx.selectedOverlay
        overlay = self.__overlayList[ovlIdx]

        if overlay is None:
            return

        # TODO support for other overlay types
        if type(overlay) != fslimage.Image:
            raise RuntimeError('Currently, only {} instances can be '
                               'copied'.format(fslimage.Image.__name__))

        display = self.__displayCtx.getDisplay(overlay)
        opts    = self.__displayCtx.getOpts(   overlay)

        # We ask the user questions three:
        #  - Copy data, or create an empty (a.k.a. mask) image?
        #  - Copy display settings?
        #  - For 4D, copy 4D, or just the current 3D volume?
        #
        # Here we build a list of
        # questions and initial states.
        options = []
        states  = []

        createMaskSetting  = 'fsleyes.actions.copyoverlay.createMask'
        copyDisplaySetting = 'fsleyes.actions.copyoverlay.copyDisplay'
        copy4DSetting      = 'fsleyes.actions.copyoverlay.copy4D'

        createMask  = fslsettings.read(createMaskSetting,  False)
        copyDisplay = fslsettings.read(copyDisplaySetting, False)
        copy4D      = fslsettings.read(copy4DSetting,      False)
        is4D        = len(overlay.shape) > 3 and overlay.shape[3] > 1

        # the settings module is not yet type-aware
        createMask  = fslsettings.strToBool(createMask)
        copyDisplay = fslsettings.strToBool(copyDisplay)
        copy4D      = fslsettings.strToBool(copy4D)

        options.append(strings.messages['actions.copyoverlay.createMask'])
        states .append(createMask)

        options.append(strings.messages['actions.copyoverlay.copyDisplay'])
        states .append(copyDisplay)

        if is4D:
            options.append(strings.messages['actions.copyoverlay.copy4D'])
            states .append(copy4D)

        # Ask the user what they want to do
        dlg = fsldlg.CheckBoxMessageDialog(
            self.__frame,
            title=strings.actions[self],
            message='Copy {}'.format(display.name),
            cbMessages=options,
            cbStates=states,
            okBtnText='OK',
            cancelBtnText='Cancel')

        if dlg.ShowModal() != wx.ID_OK:
            return

        createMask  = dlg.CheckBoxState(0)
        copyDisplay = dlg.CheckBoxState(1)
        if is4D:
            copy4D = dlg.CheckBoxState(2)

        fslsettings.write(createMaskSetting,  createMask)
        fslsettings.write(copyDisplaySetting, copyDisplay)
        if is4D:
            fslsettings.write(copy4DSetting, copy4D)

        # Extract/create the data for the new image.
        # Set copy4D to true for 3D images, just to
        # make the 4th dimension indexing below work.
        if not is4D:
            copy4D = True

        if createMask:
            if copy4D: data = np.zeros(overlay.shape)
            else:      data = np.zeros(overlay.shape[:3])
        else:
            if copy4D: data = np.copy(overlay[:])
            else:      data = np.copy(overlay[:, :, :, opts.volume])

        # Create the copy, put it in the list
        header = overlay.header
        name   = '{}_copy'.format(overlay.name)
        copy   = fslimage.Image(data, name=name, header=header)
        
        self.__overlayList.insert(ovlIdx + 1, copy)
        
        # Copy the Display/DisplayOpts settings
        if copyDisplay:

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

                # But don't clobber the transform, and related,
                # properties, as it is (typically) automatically
                # controlled via the DisplayContext.displaySpace
                if prop in ('transform', 'bounds', 'customXform'):
                    continue
                
                val = getattr(srcOpts, prop)
                setattr(destOpts, prop, val)
