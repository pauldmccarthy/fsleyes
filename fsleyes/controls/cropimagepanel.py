#!/usr/bin/env python
#
# cropimagepanel.py - The CropImagePanel class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx

import fsl.utils.async             as async
import fsl.data.image              as fslimage

import fsleyes_props               as props
import fsleyes_widgets.rangeslider as rslider

import fsleyes.panel               as fslpanel
import fsleyes.displaycontext      as displaycontext
import fsleyes.strings             as strings
import fsleyes.actions.copyoverlay as copyoverlay


class CropImagePanel(fslpanel.FSLeyesPanel):
    """The ``CropImagePanel`` class is a FSLeyes control for use in an
    :class:`.OrthoPanel`, with the associated :class:`.CropImageProfile`.
    It contains controls allowing the user to define a cropping box
    for the currently selected overlay (if it is an :class:`.Image`),
    and "Crop" and "Cancel" buttons.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """Create a ``CropImagePanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        profile = ortho.getCurrentProfile()

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

        self.__cropLabel       = wx.StaticText(self)
        self.__sizeLabel       = wx.StaticText(self)
        self.__cropButton      = wx.Button(    self, id=wx.ID_OK)
        self.__robustFovButton = wx.Button(    self)
        self.__cancelButton    = wx.Button(    self, id=wx.ID_CANCEL)

        self.__cropButton     .SetLabel(strings.labels[self, 'cropButton'])
        self.__robustFovButton.SetLabel(strings.labels[self,
                                                       'robustFovButton'])
        self.__cancelButton   .SetLabel(strings.labels[self, 'cancelButton'])

        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__sizer.Add((1, 10))
        self.__sizer.Add(self.__cropLabel,     flag=wx.CENTRE, proportion=1)
        self.__sizer.Add((1, 10))
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
        self.__btnSizer.Add(self.__cancelButton,    flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),                flag=wx.EXPAND,
                            proportion=1)

        self.SetSizer(self.__sizer)
        self.SetMinSize(self.__sizer.GetMinSize())
        self.__cropButton.SetDefault()

        self.__cropButton  .Bind(wx.EVT_BUTTON,          self.__onCrop)
        self.__cancelButton.Bind(wx.EVT_BUTTON,          self.__onCancel)
        self.__volumeWidget.Bind(rslider.EVT_RANGE,      self.__onVolume)
        self.__volumeWidget.Bind(rslider.EVT_LOW_RANGE,  self.__onVolume)
        self.__volumeWidget.Bind(rslider.EVT_HIGH_RANGE, self.__onVolume)

        profile.robustfov.bindToWidget(self,
                                       wx.EVT_BUTTON,
                                       self.__robustFovButton)

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        profile    .addListener('cropBox',
                                self._name,
                                self.__cropBoxChanged)

        self.__selectedOverlayChanged()
        self.__cropBoxChanged()


    def destroy(self):
        """Must be called when this ``CropImagePanel`` is no longer needed.
        Removes property listeners and clears references.
        """

        profile     = self.__profile
        displayCtx  = self.getDisplayContext()
        overlayList = self.getOverlayList()

        profile    .removeListener('cropBox',         self._name)
        displayCtx .removeListener('selectedOverlay', self._name)
        overlayList.removeListener('overlays',        self._name)

        self.__ortho   = None
        self.__profile = None

        fslpanel.FSLeyesPanel.destroy(self)


    def __registerOverlay(self, overlay):
        """Called by :meth:`__selectedOverlayChanged`. Registers the
        given overlay.
        """

        self.__overlay = overlay

        display = self.getDisplayContext().getDisplay(overlay)

        is4D = len(overlay.shape) == 4 and overlay.shape[3] > 1

        if is4D:
            self.__volumeWidget.SetLimits(0, overlay.shape[3])
            self.__volumeWidget.SetRange( 0, overlay.shape[3])

        self.__volumeWidget.Enable(is4D)

        display.addListener('name', self._name, self.__overlayNameChanged)
        self.__overlayNameChanged()


    def __deregisterOverlay(self):
        """Called by :meth:`__selectedOverlayChanged`. Deregisters the
        current overlay.
        """

        if self.__overlay is None:
            return

        try:
            display = self.getDisplayContext().getDisplay(self.__overlay)
            display.removeListener('name', self._name)

        except displaycontext.InvalidOverlayError:
            pass

        self.__cropLabel.SetLabel(strings.labels[self, 'image.noImage'])

        self.__overlay = None


    def __overlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` of the currently selected
        overlay changes. Updates the name label.
        """

        display = self.getDisplayContext().getDisplay(self.__overlay)
        label   = strings.labels[self, 'image']
        label   = label.format(display.name)
        self.__cropLabel.SetLabel(label)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Updates labels appropriately.
        """

        displayCtx = self.getDisplayContext()
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
        is4D    = len(overlay.shape) == 4 and overlay.shape[3] > 1
        xlen    = profile.cropBox.xlen
        ylen    = profile.cropBox.ylen
        zlen    = profile.cropBox.zlen
        tlo     = self.__volumeWidget.GetLow()
        thi     = self.__volumeWidget.GetHigh()
        tlen    = thi - tlo

        if is4D:
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


    def __onCancel(self, ev=None):
        """Called when the Cancel button is pushed. Calls
        :meth:`.OrthoPanel.toggleCropMode` - this will result in
        this ``CropImagePanel`` being destroyed.

        This method is also called programmatically from the :meth:`__onCrop`
        method after the image is cropped.
        """

        # Do asynchronously, because we don't want
        # this CropImagePanel being destroyed from
        # its own event handler.
        async.idle(self.__ortho.toggleCropMode)


    def __onCrop(self, ev):
        """Crops the selected image. This is done via a call to
        :func:`.copyoverlay.copyImage`. Also calls :meth:`__onCancel`,
        to finish cropping.
        """

        overlayList = self.getOverlayList()
        displayCtx  = self.getDisplayContext()
        overlay     = displayCtx.getSelectedOverlay()
        is4D        = len(overlay.shape) == 4 and overlay.shape[3] > 1
        display     = displayCtx.getDisplay(overlay)
        name        = '{}_roi'.format(display.name)
        cropBox     = self.__profile.cropBox
        roi         = [cropBox.x,
                       cropBox.y,
                       cropBox.z]

        if is4D:
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
