#!/usr/bin/env python
#
# copyoverlay.py - Action which copies the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CopyOverlayAction`, a global action
which creates a copy of the currently selected overlay.
"""


import numpy                  as np

import fsl.data.image         as fslimage
import fsl.utils.transform    as transform
import fsl.utils.settings     as fslsettings
import fsleyes_widgets.dialog as fsldlg
import fsleyes.strings        as strings
from . import                    base


class CopyOverlayAction(base.Action):
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
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__copyOverlay)

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
        base.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list, changes.

        Enables/disables this action depending on the nature of the selected
        overlay.
        """

        ovl          = self.__displayCtx.getSelectedOverlay()
        self.enabled = (ovl is not None) and isinstance(ovl, fslimage.Image)


    def __copyOverlay(self):
        """Creates a copy of the currently selected overlay, and inserts it
        into the :class:`.OverlayList`.
        """

        import wx

        overlay = self.__displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        # TODO support for other overlay types
        if type(overlay) != fslimage.Image:
            raise RuntimeError('Currently, only {} instances can be '
                               'copied'.format(fslimage.Image.__name__))

        display = self.__displayCtx.getDisplay(overlay)

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
            yesText='OK',
            cancelText='Cancel',
            focus='yes')

        if dlg.ShowModal() != wx.ID_YES:
            return

        createMask  = dlg.CheckBoxState(0)
        copyDisplay = dlg.CheckBoxState(1)
        if is4D:
            copy4D = dlg.CheckBoxState(2)

        fslsettings.write(createMaskSetting,  createMask)
        fslsettings.write(copyDisplaySetting, copyDisplay)
        if is4D:
            fslsettings.write(copy4DSetting, copy4D)

        copyImage(self.__overlayList,
                  self.__displayCtx,
                  overlay,
                  createMask=createMask,
                  copy4D=copy4D,
                  copyDisplay=copyDisplay)


def copyImage(overlayList,
              displayCtx,
              overlay,
              createMask=False,
              copy4D=True,
              copyDisplay=True,
              name=None,
              roi=None,
              data=None):
    """Creates a copy of the given :class:`.Image` overlay, and inserts it
    into the :class:`.OverlayList`.

    :arg overlayList: The :class:`.OverlayList`.

    :arg displayCtx:  The :class:`.DisplayContext`.

    :arg overlay:     The :class:`.Image` to be copied.

    :arg createMask:  If ``True``, the copy will be an empty ``Image`` the
                      same shape as the ``overlay``.

    :arg copy4D:      If ``True``, and the ``overlay`` is 4D, the copy will
                      also be 4D. Otherwise, the current 3D voluem is copied.

    :arg copyDisplay: If ``True``, the copy will inherit the display settings
                      of the ``overlay``. Otherwise, the copy will be
                      initialised  with default display settings.

    :arg name:        If provided, will be used as the :attr:`.Display.name`
                      of the copy. Otherwise the copy will be given a name.

    :arg roi:         If provided, the copy will be cropped to the low/high
                      voxel bounds specified in the image. Must be a sequence
                      of tuples, containing the low/high bounds for each voxel
                      dimension. For 4D images, the bounds for the fourth
                      dimension are optional.

    :arg data:        If provided, is used as the image data for the new copy.
                      Must match the shape dictated by the other arguments
                      (i.e. ``copy4D`` and ``roi``). If ``data`` is provided,
                      the ``createMask`` argument is ignored.
    """

    ovlIdx = overlayList.index(overlay)
    opts   = displayCtx.getOpts(overlay)
    isROI  = roi is not None
    is4D   = len(overlay.shape) > 3 and overlay.shape[3] > 1

    if name is None:
        name = '{}_copy'.format(overlay.name)

    if roi is None:
        roi = [(0, s) for s in overlay.shape]

    # If the image is 4D, and an ROI of
    # length 3 has been given, add some
    # bounds for the fourth dimension
    if is4D and copy4D and len(roi) == 3:
        roi = list(roi) + [(0, overlay.shape[3])]

    # If we are only supposed to copy
    # the current 3D volume of a 4D
    # image, adjust the ROI accordingly.
    if is4D and not copy4D:
        roi = list(roi[:3]) + [(opts.volume, opts.volume + 1)]

    shape = [hi - lo for lo, hi in roi]
    slc   = tuple([slice(lo, hi) for lo, hi in roi])

    if data is not None: pass
    elif createMask:     data = np.zeros(shape)
    else:                data = np.copy(overlay[slc])

    # If this is an ROI, we need to add
    # an offset to the image affine
    if isROI:
        xform  = overlay.voxToWorldMat
        offset = [lo for lo, hi in roi[:3]]
        offset = transform.scaleOffsetXform([1, 1, 1], offset)
        xform  = transform.concat(xform, offset)

    else:
        xform  = None

    # Create the copy, put it in the list
    header = overlay.header.copy()
    copy   = fslimage.Image(data, name=name, header=header, xform=xform)

    overlayList.insert(ovlIdx + 1, copy)

    # Copy the Display/DisplayOpts settings
    if copyDisplay:

        srcDisplay  = displayCtx.getDisplay(overlay)
        destDisplay = displayCtx.getDisplay(copy)

        for prop in srcDisplay.getAllProperties()[0]:

            # Don't override the name
            # that we set above
            if prop == 'name':
                continue

            val = getattr(srcDisplay, prop)
            setattr(destDisplay, prop, val)

        # And after the Display has been configured
        # copy the DisplayOpts settings.
        srcOpts  = displayCtx.getOpts(overlay)
        destOpts = displayCtx.getOpts(copy)

        for prop in srcOpts.getAllProperties()[0]:

            # But don't clobber the transform, and related,
            # properties, as it is (typically) automatically
            # controlled via the DisplayContext.displaySpace
            if prop in ('transform', 'bounds', 'customXform'):
                continue

            val = getattr(srcOpts, prop)
            setattr(destOpts, prop, val)
