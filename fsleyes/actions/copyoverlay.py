#!/usr/bin/env python
#
# copyoverlay.py - Action which copies the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CopyOverlayAction`, a global action
which creates a copy of the currently selected overlay.
"""


import numpy as np

import fsl.data.image         as fslimage
import fsl.utils.settings     as fslsettings
import fsl.utils.image.roi    as imgroi
import fsleyes_widgets.dialog as fsldlg
import fsleyes.strings        as strings
from . import                    base


class CopyOverlayAction(base.NeedOverlayAction):
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
        base.NeedOverlayAction.__init__(
            self, overlayList, displayCtx, func=self.__copyOverlay)
        self.__frame = frame


    def __copyOverlay(self):
        """Creates a copy of the currently selected overlay, and inserts it
        into the :class:`.OverlayList`.
        """

        import wx

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        # TODO support for other overlay types
        if type(overlay) != fslimage.Image:
            raise RuntimeError('Currently, only {} instances can be '
                               'copied'.format(fslimage.Image.__name__))

        display = self.displayCtx.getDisplay(overlay)

        # We ask the user questions four:
        #  - Copy data, or create an empty (a.k.a. mask) image?
        #  - Copy display settings?
        #  - For 4D, copy 4D, or just the current 3D volume?
        #  - For complex/RGB(A), copy as single channel, or multi-channel?
        #
        # Here we build a list of
        # questions and initial states.
        options = []
        states  = []

        createMaskSetting  = 'fsleyes.actions.copyoverlay.createMask'
        copyDisplaySetting = 'fsleyes.actions.copyoverlay.copyDisplay'
        copy4DSetting      = 'fsleyes.actions.copyoverlay.copy4D'
        copyMultiSetting   = 'fsleyes.actions.copyoverlay.copyMulti'

        createMask  = fslsettings.read(createMaskSetting,  False)
        copyDisplay = fslsettings.read(copyDisplaySetting, False)
        copy4D      = fslsettings.read(copy4DSetting,      False)
        copyMulti   = fslsettings.read(copy4DSetting,      True)
        is4D        = len(overlay.shape) > 3 and overlay.shape[3] > 1
        isMulti     = overlay.iscomplex or overlay.nvals > 1

        options.append(strings.messages['actions.copyoverlay.createMask'])
        states .append(createMask)

        options.append(strings.messages['actions.copyoverlay.copyDisplay'])
        states .append(copyDisplay)

        if is4D:
            options.append(strings.messages['actions.copyoverlay.copy4D'])
            states .append(copy4D)

        if isMulti:
            options.append(strings.messages['actions.copyoverlay.copyMulti'])
            states .append(copyMulti)

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

        createMask            = dlg.CheckBoxState(0)
        copyDisplay           = dlg.CheckBoxState(1)
        if is4D:    copy4D    = dlg.CheckBoxState(2)
        if isMulti: copyMulti = dlg.CheckBoxState(3 if is4D else 2)

        fslsettings            .write(createMaskSetting,  createMask)
        fslsettings            .write(copyDisplaySetting, copyDisplay)
        if is4D:    fslsettings.write(copy4DSetting,      copy4D)
        if isMulti: fslsettings.write(copyMultiSetting,   copyMulti)

        # If the user de-selected copy all channels,
        # ask them which channel they want to copy
        channel = None
        if isMulti and (not copyMulti):
            if overlay.iscomplex:
                choices = ['real', 'imag']
            else:
                choices = ['R' ,'G', 'B', 'A'][:overlay.nvals]

            labels = [strings.choices[self, 'component'][c] for c in choices]
            title  = strings.titles[  'actions.copyoverlay.component']
            msg    = strings.messages['actions.copyoverlay.component']
            dlg    = wx.SingleChoiceDialog(self.__frame,
                                           msg,
                                           title,
                                           choices=labels)

            if dlg.ShowModal() != wx.ID_OK:
                return

            channel = choices[dlg.GetSelection()]

        copyImage(self.overlayList,
                  self.displayCtx,
                  overlay,
                  createMask=createMask,
                  copy4D=copy4D,
                  channel=channel,
                  copyDisplay=copyDisplay)


def copyImage(overlayList,
              displayCtx,
              overlay,
              createMask=False,
              copy4D=True,
              copyDisplay=True,
              name=None,
              roi=None,
              channel=None,
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
                      dimension are optional. If ``roi`` specifies more than
                      three dimensions, but ``copy4D is False``, the additional
                      dimensions are ignored.

    :arg channel:     If provided, and if the image is complex or multi-valued
                      (RGB(A)), only this channel is copied. Otherwise the
                      image and data type are copied as-is. For complex images,
                      valid values are ``'real'`` or ``'imag'``; for multi-
                      valued images, valid values are ``'R'``, ``'G'``, ``'B'``
                      or ``'A'``.

    :arg data:        If provided, is used as the image data for the new copy.
                      Must match the shape dictated by the other arguments
                      (i.e. ``copy4D`` and ``roi``). If ``data`` is provided,
                      the ``createMask`` argument is ignored.

    :returns:         The newly created :class:`.Image` object.


    Note that the ``roi`` and ``copy4D`` options do not support images with
    more than four dimensions.
    """

    ovlIdx     = overlayList.index(overlay)
    opts       = displayCtx.getOpts(overlay)
    is4D       = len(overlay.shape) > 3
    isROI      = roi is not None
    copy4D     = copy4D and is4D
    createMask = createMask and (data is None)

    # Initialise the roi indices if one wasn't
    # provided - we will use the indices
    # regardless of whether an ROI was passed
    # in or not
    if roi is None:
        roi = [(0, s) for s in overlay.shape]

    # Adjust the roi to index a
    # specific volume if requested
    if not copy4D:
        roi = list(roi[:3]) + [(i, i + 1) for i in opts.index()[3:]]

    if name is None:
        name = '{}_copy'.format(overlay.name)

    # If an ROI is not specified, we slice
    # the image data, either including all
    # volumes, or the currently selected volume
    if not isROI:
        slc     = tuple(slice(lo, hi) for lo, hi in roi)
        imgdata = overlay[slc]
        xform   = overlay.voxToWorldMat

    # if an ROI is specified, we use the
    # fsl.utils.image.roi module to generate
    # an ROI and the adjusted voxel-to-world
    # affine
    else:
        roi     = imgroi.roi(overlay, roi)
        imgdata = roi.data
        xform   = roi.voxToWorldMat

    if channel is not None:
        if overlay.iscomplex:
            if   channel == 'real': imgdata = imgdata.real
            elif channel == 'imag': imgdata = imgdata.imag
            else: raise ValueError('Invalid value for channel: '
                                   '{}'.format(channel))
        elif overlay.nvals > 1:
            if channel not in 'RGBA':
                raise ValueError('Invalid value for channel: '
                                   '{}'.format(channel))
            imgdata = imgdata[channel]

    if createMask:
        data = np.zeros(imgdata.shape, dtype=imgdata.dtype)
    elif data is None:
        data = np.copy(imgdata)

    copy = fslimage.Image(data,
                          xform=xform,
                          header=overlay.header,
                          name=name)

    overlayList.insert(ovlIdx + 1, copy)

    # Copy the Display/DisplayOpts settings
    if copyDisplay:

        # Don't override the name
        # that we set above
        dispexcl = ('name',)

        # And don't clobber the transform, and related,
        # properties, as it is (typically) automatically
        # controlled via the DisplayContext.displaySpace
        optexcl = ('transform', 'bounds')

        copyDisplayProperties(displayCtx,
                              overlay,
                              copy,
                              displayExclude=dispexcl,
                              optExclude=optexcl)

    return copy


def copyDisplayProperties(displayCtx,
                          src,
                          dest,
                          displayExclude=None,
                          optExclude=None,
                          displayArgs=None,
                          optArgs=None):
    """Copies all properties from the ``src`` :class:`.Display` and
    :class:`.DisplayOpts` instances to the ``dest`` instances.

    :arg displayCtx:     The :class:`.DisplayContext`

    :arg displayExclude: Collection of :class:`.Display` properties which
                         should not be copied

    :arg optExclude:     Collection of :class:`.DisplayOpts` properties which
                         should not be copied

    :arg displayArgs:    Values to be used instead of the ``src`` ``Display``
                         values.

    :arg optArgs:        Values to be used instead of the ``src``
                         ``DisplayOpts`` values.
    """

    if displayExclude is None: displayExclude = []
    if optExclude     is None: optExclude     = []
    if displayArgs    is None: displayArgs    = {}
    if optArgs        is None: optArgs        = {}

    # copy the Display properties first, as
    # they may affect the DisplayOpts type
    srcDisplay  = displayCtx.getDisplay(src)
    destDisplay = displayCtx.getDisplay(dest)

    for prop in srcDisplay.getAllProperties()[0]:

        if prop in displayExclude:
            continue

        if (not srcDisplay .propertyIsEnabled(prop)) or \
           (not destDisplay.propertyIsEnabled(prop)):
            continue

        val = displayArgs.get(prop, getattr(srcDisplay, prop))

        # Check that the overlay type of the old
        # overlay is valid for the new overlay
        if prop == 'overlayType':
            choices = destDisplay.getProp('overlayType').getChoices(destDisplay)
            if val not in choices:
                continue

        setattr(destDisplay, prop, val)

    # And after the Display has been configured
    # copy the DisplayOpts settings.
    srcOpts  = displayCtx.getOpts(src)
    destOpts = displayCtx.getOpts(dest)

    for prop in srcOpts.getAllProperties()[0]:

        if prop in optExclude:
            continue

        # The source and destination opts
        # instances may be different types
        if not hasattr(destOpts, prop):
            continue

        if (not srcOpts .propertyIsEnabled(prop)) or \
           (not destOpts.propertyIsEnabled(prop)):
            continue

        val = optArgs.get(prop, getattr(srcOpts, prop))
        setattr(destOpts, prop, val)
