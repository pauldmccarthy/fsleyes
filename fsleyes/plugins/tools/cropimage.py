#!/usr/bin/env python
#
# cropimage.py - The CropImagePanel class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CropImagePanel` class.

The ``CropImagePanel`` is a a FSLeyes control which is used in conjunction
with the :class:`.OrthoCropProfile`, allowing the user to crop an image.
This module also provides the standalone :func:`loadCropParameters` function,
for loading cropping parameters from a file.
"""


import              os
import os.path   as op
import itertools as it
import              wx
import numpy     as np

import fsl.utils.idle                            as idle
import fsl.data.image                            as fslimage

import fsleyes_props                             as props
import fsleyes_widgets.rangeslider               as rslider
import fsleyes_widgets.utils.status              as status

import fsleyes.controls.controlpanel             as ctrlpanel
import fsleyes.displaycontext                    as displaycontext
import fsleyes.views.orthopanel                  as orthopanel
import fsleyes.strings                           as strings
import fsleyes.actions                           as actions
import fsleyes.actions.copyoverlay               as copyoverlay
import fsleyes.controls.displayspacewarning      as dswarning
import fsleyes.plugins.profiles.orthocropprofile as orthocropprofile


class CropImageAction(actions.ToggleControlPanelAction):
    """The ``CropImageAction`` just toggles a :class:`.CropImagePanel`. It is
    added under the FSLeyes Tools menu.
    """

    @staticmethod
    def supportedViews():
        """The ``CropImageAction`` is restricted for use with
        :class:`.OrthoPanel` views.
        """
        return [orthopanel.OrthoPanel]


    def __init__(self, overlayList, displayCtx, ortho):
        """Create  ``CropImageAction``. """
        super().__init__(overlayList, displayCtx, ortho, CropImagePanel)
        self.__ortho = ortho
        self.__name  = '{}_{}'.format(type(self).__name__, id(self))

        displayCtx.addListener('selectedOverlay', self.__name,
                               self.__selectedOverlayChanged)


    def destroy(self):
        """Called when the :class:`.OrthoPanel` that owns this action is
        closed. Clears references, removes listeners, and calls the base
        class ``destroy`` method.
        """
        if self.destroyed:
            return

        self.__ortho = None
        self.displayCtx.removeListener('selectedOverlay', self.__name)
        super().destroy()


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay changes. Enables/disables this
        action (and hence the bound Tools menu item) depending on whether the
        overlay is an image.
        """
        ovl = self.displayCtx.getSelectedOverlay()
        self.enabled = isinstance(ovl, fslimage.Image)


class CropImagePanel(ctrlpanel.ControlPanel):
    """The ``CropImagePanel`` class is a FSLeyes control for use in an
    :class:`.OrthoPanel`, with the associated :class:`.CropImageProfile`.  It
    contains controls allowing the user to define a cropping box for the
    currently selected overlay (if it is an :class:`.Image`), and "Crop",
    "Load", "Save", and "Cancel" buttons.
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``CropImagePanel`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


    @staticmethod
    def ignoreControl():
        """Tells FSLeyes not to add the ``CropImagePanel`` as an option to
        the Settings menu. Instead, the :class:`CropImageAction` is added as
        an option to the Tools menu.
        """
        return True


    @staticmethod
    def profileCls():
        """Returns the :class:`.OrthoCropProfile` class, which needs to be
        activated in conjunction with the ``CropImagePanel``.
        """
        return orthocropprofile.OrthoCropProfile


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'floatPane' : True,
                'floatOnly' : True}



    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create a ``CropImagePanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, ortho)

        profile = ortho.currentProfile

        self.__ortho   = ortho
        self.__profile = profile
        self.__overlay = None

        self.__cropBoxWidget = props.makeWidget(
            self,
            profile,
            'cropBox',
            showLimits=False,
            labels=['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax'])

        self.__volumeWidget = rslider.RangeSliderSpinPanel(
            self,
            minValue=0,
            maxValue=1,
            minDistance=1,
            lowLabel='tmin',
            highLabel='tmax',
            style=rslider.RSSP_INTEGER)

        self.__dsWarning = dswarning.DisplaySpaceWarning(
            self,
            overlayList,
            displayCtx,
            ortho.frame,
            strings.messages[self, 'dsWarning'],
            'not like overlay',
            'overlay')

        self.__cropLabel       = wx.StaticText(self)
        self.__sizeLabel       = wx.StaticText(self)
        self.__cropButton      = wx.Button(    self, id=wx.ID_OK)
        self.__robustFovButton = wx.Button(    self)
        self.__loadButton      = wx.Button(    self)
        self.__saveButton      = wx.Button(    self)
        self.__cancelButton    = wx.Button(    self, id=wx.ID_CANCEL)

        self.__cropButton     .SetLabel(strings.labels[self, 'crop'])
        self.__robustFovButton.SetLabel(strings.labels[self, 'robustFov'])
        self.__loadButton     .SetLabel(strings.labels[self, 'load'])
        self.__saveButton     .SetLabel(strings.labels[self, 'save'])
        self.__cancelButton   .SetLabel(strings.labels[self, 'cancel'])

        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__sizer.Add((1, 10))
        self.__sizer.Add(self.__cropLabel,     flag=wx.CENTRE)
        self.__sizer.Add((1, 10))
        self.__sizer.Add(self.__dsWarning,     flag=wx.CENTRE)
        self.__sizer.Add((1, 10), proportion=1)
        self.__sizer.Add(self.__cropBoxWidget, flag=wx.EXPAND)
        self.__sizer.Add(self.__volumeWidget,  flag=wx.EXPAND)
        self.__sizer.Add((1, 10))
        self.__sizer.Add(self.__sizeLabel,     flag=wx.CENTRE, proportion=1)
        self.__sizer.Add((1, 10))
        self.__sizer.Add(self.__btnSizer,      flag=wx.CENTRE)
        self.__sizer.Add((1, 10))

        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND,
                            proportion=1)
        self.__btnSizer.Add(self.__cropButton,      flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND)
        self.__btnSizer.Add(self.__robustFovButton, flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND)
        self.__btnSizer.Add(self.__loadButton,      flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND)
        self.__btnSizer.Add(self.__saveButton,      flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND)
        self.__btnSizer.Add(self.__cancelButton,    flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND,
                            proportion=1)

        self.SetSizer(self.__sizer)
        self.SetMinSize(self.__sizer.GetMinSize())
        self.__cropButton.SetDefault()

        self.__cropButton  .Bind(wx.EVT_BUTTON,          self.__onCrop)
        self.__loadButton  .Bind(wx.EVT_BUTTON,          self.__onLoad)
        self.__saveButton  .Bind(wx.EVT_BUTTON,          self.__onSave)
        self.__cancelButton.Bind(wx.EVT_BUTTON,          self.__onCancel)
        self.__volumeWidget.Bind(rslider.EVT_RANGE,      self.__onVolume)
        self.__volumeWidget.Bind(rslider.EVT_LOW_RANGE,  self.__onVolume)
        self.__volumeWidget.Bind(rslider.EVT_HIGH_RANGE, self.__onVolume)

        profile.robustfov.bindToWidget(self,
                                       wx.EVT_BUTTON,
                                       self.__robustFovButton)

        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)
        profile    .addListener('cropBox',
                                self.name,
                                self.__cropBoxChanged)

        self.__selectedOverlayChanged()
        self.__cropBoxChanged()


    def destroy(self):
        """Must be called when this ``CropImagePanel`` is no longer needed.
        Removes property listeners and clears references.
        """

        profile     = self.__profile
        displayCtx  = self.displayCtx
        overlayList = self.overlayList
        dsWarning   = self.__dsWarning

        profile    .removeListener('cropBox',         self.name)
        displayCtx .removeListener('selectedOverlay', self.name)
        overlayList.removeListener('overlays',        self.name)

        self.__ortho     = None
        self.__profile   = None
        self.__dsWarning = None

        dsWarning.destroy()
        ctrlpanel.ControlPanel.destroy(self)


    def __registerOverlay(self, overlay):
        """Called by :meth:`__selectedOverlayChanged`. Registers the
        given overlay.
        """

        self.__overlay = overlay

        display = self.displayCtx.getDisplay(overlay)
        is4D    = overlay.ndim >= 4

        if is4D:
            self.__volumeWidget.SetLimits(0, overlay.shape[3])
            self.__volumeWidget.SetRange( 0, overlay.shape[3])

        self.__volumeWidget.Enable(is4D)

        display.addListener('name', self.name, self.__overlayNameChanged)
        self.__overlayNameChanged()


    def __deregisterOverlay(self):
        """Called by :meth:`__selectedOverlayChanged`. Deregisters the
        current overlay.
        """

        if self.__overlay is None:
            return

        try:
            display = self.displayCtx.getDisplay(self.__overlay)
            display.removeListener('name', self.name)

        except displaycontext.InvalidOverlayError:
            pass

        self.__cropLabel.SetLabel(strings.labels[self, 'image.noImage'])

        self.__overlay = None


    def __overlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` of the currently selected
        overlay changes. Updates the name label.
        """

        display = self.displayCtx.getDisplay(self.__overlay)
        label   = strings.labels[self, 'image']
        label   = label.format(display.name)
        self.__cropLabel.SetLabel(label)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Updates labels appropriately.
        """

        displayCtx = self.displayCtx
        overlay    = displayCtx.getSelectedOverlay()

        if overlay is self.__overlay:
            return

        self.__deregisterOverlay()

        if not isinstance(overlay, fslimage.Image):
            self.Disable()
        else:
            self.Enable()
            self.__registerOverlay(overlay)


    def __updateSizeLabel(self):
        """Called by the crop region and volume widget event handlers. Updates
        a label which displays the current crop region size.
        """

        overlay = self.__overlay
        profile = self.__profile
        xlen    = profile.cropBox.xlen
        ylen    = profile.cropBox.ylen
        zlen    = profile.cropBox.zlen
        tlo     = self.__volumeWidget.GetLow()
        thi     = self.__volumeWidget.GetHigh()
        tlen    = thi - tlo

        if overlay.ndim >= 4:
            label = strings.labels[self, 'cropSize4d']
            label = label.format(xlen, ylen, zlen, tlen)
        else:
            label = strings.labels[self, 'cropSize3d']
            label = label.format(xlen, ylen, zlen)

        self.__sizeLabel.SetLabel(label)


    def __cropBoxChanged(self, *a):
        """Called when the :attr:`.OrthoCropProfile.cropBox` changes.
        Updates labels appropriately.
        """
        self.__updateSizeLabel()


    def __onVolume(self, ev):
        """Called when the user changes the volume limit, for 4D images.
        Updates the label which displays the crop region size.
        """
        self.__updateSizeLabel()


    def __onLoad(self, ev):
        """Called when the Save button is pushed. Prompts the user to select
        a file to load crop parameters from.
        """

        overlay  = self.__overlay
        cropBox  = self.__profile.cropBox
        fileName = '{}_crop.txt'.format(overlay.name)

        if overlay.dataSource is not None:
            dirName = op.dirname(overlay.dataSource)
        else:
            dirName = os.getcwd()

        if not op.exists(op.join(dirName, fileName)):
            fileName = ''

        dlg = wx.FileDialog(
            self,
            defaultDir=dirName,
            defaultFile=fileName,
            message=strings.messages[self, 'saveCrop'],
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()
        errTitle = strings.titles[  self, 'loadError']
        errMsg   = strings.messages[self, 'loadError']

        with status.reportIfError(errTitle, errMsg, raiseError=False):

            params     = loadCropParameters(filePath, overlay)
            cropBox[:] = params[:6]

            if overlay.ndim >= 4:
                tlo, thi = params[6:]
                self.__volumeWidget.SetLow(tlo)
                self.__volumeWidget.SetHigh(thi)


    def __onSave(self, ev):
        """Called when the Save button is pushed. Saves the current crop
        parameters to a text file.
        """

        overlay  = self.__overlay
        cropBox  = self.__profile.cropBox
        fileName = '{}_crop.txt'.format(overlay.name)

        if overlay.dataSource is not None:
            dirName = op.dirname(overlay.dataSource)
        else:
            dirName = os.getcwd()

        dlg = wx.FileDialog(
            self,
            defaultDir=dirName,
            defaultFile=fileName,
            message=strings.messages[self, 'saveCrop'],
            style=wx.FD_SAVE)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()

        # The crop parameters are saved
        # in a fslroi-compatible manner.
        params = [cropBox.xlo,
                  cropBox.xhi - cropBox.xlo,
                  cropBox.ylo,
                  cropBox.yhi - cropBox.ylo,
                  cropBox.zlo,
                  cropBox.zhi - cropBox.zlo]

        if overlay.ndim >= 4:
            tlo     = self.__volumeWidget.GetLow()
            thi     = self.__volumeWidget.GetHigh()
            params.extend((tlo, thi - tlo))

        errTitle = strings.titles[  self, 'saveError']
        errMsg   = strings.messages[self, 'saveError']

        with status.reportIfError(errTitle, errMsg, raiseError=False):
            np.savetxt(filePath, [params], fmt='%i')


    def __onCancel(self, ev=None):
        """Called when the Cancel button is pushed. Calls
        :meth:`.OrthoPanel.togglePanel` - this will result in
        this ``CropImagePanel`` being destroyed.

        This method is also called programmatically from the :meth:`__onCrop`
        method after the image is cropped.
        """

        # Do asynchronously, because we don't want
        # this CropImagePanel being destroyed from
        # its own event handler.
        idle.idle(self.__ortho.togglePanel, CropImagePanel)


    def __onCrop(self, ev):
        """Crops the selected image. This is done via a call to
        :func:`.copyoverlay.copyImage`. Also calls :meth:`__onCancel`,
        to finish cropping.
        """

        overlayList = self.overlayList
        displayCtx  = self.displayCtx
        overlay     = displayCtx.getSelectedOverlay()
        display     = displayCtx.getDisplay(overlay)
        name        = '{}_roi'.format(display.name)
        cropBox     = self.__profile.cropBox
        roi         = [cropBox.x,
                       cropBox.y,
                       cropBox.z]

        if overlay.ndim >= 4:
            roi.append(self.__volumeWidget.GetRange())

        copyoverlay.copyImage(
            overlayList,
            displayCtx,
            overlay,
            createMask=False,
            copy4D=True,
            copyDisplay=True,
            name=name,
            roi=roi)

        self.__onCancel()


def loadCropParameters(filename, overlay):
    """Load in crop values from a text file assumed to contain ``fslroi``-
    compatible parameters. Any parameters which may be passed to ``fslroi``
    are accepted::

        fslroi in out tmin tlen
        fslroi in out xmin xlen ymin ylen zmin zlen
        fslroi in out xmin xlen ymin ylen zmin zlen tmin tlen

    Any of the ``len`` parameters may be equal to -1, in which case it is
    interpreted as continuing from the low index

    :arg filename: File to load crop parameters from.
    :arg overlay:  An :class:`.Image` which is the cropping target.
    :returns:      A sequence of ``lo, hi`` crop parameters.
    """

    is4D   = overlay.ndim >= 4
    shape  = overlay.shape[:4]
    params = list(np.loadtxt(filename).flatten())

    if len(params) not in (2, 6, 8):
        raise ValueError('File contains the wrong number of crop parameters')
    if len(params) in (2, 8) and not is4D:
        raise ValueError('File contains the wrong number of crop parameters')

    if len(params) == 2:
        params = [0, -1, 0, -1, 0, -1] + params

    if is4D and len(params) == 6:
        params = params + [0, -1]

    los = []
    his = []

    for dim in range(len(shape)):

        dlo  = params[dim * 2]
        dlen = params[dim * 2 + 1]

        if dlen == -1:
            dlen = shape[dim] - dlo

        dhi = dlo + dlen

        los.append(dlo)
        his.append(dhi)

    for lo, hi, lim in zip(los, his, shape):
        if lo < 0 or hi > lim:
            raise ValueError('Crop parameters are out of bounds for image '
                             'shape ({} < 0 or {} > {}'.format(lo, hi, lim))

    return list(it.chain(*zip(los, his)))
