#!/usr/bin/env python
#
# resample.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx

import fsleyes_widgets.floatspin as floatspin
import fsl.data.image            as fslimage
import fsl.utils.transform       as transform
from . import                       base


class ResampleAction(base.Action):
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``CopyOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__resample)

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


    def __resample(self):

        ovl = self.__displayCtx.getSelectedOverlay()

        dlg = ResampleDialog(
            self.__frame,
            title=ovl.name,
            shape=ovl.shape,
            pixdim=ovl.pixdim)

        if dlg.ShowModal() != wx.ID_OK:
            return

        # TODO interpolation option
        oldShape  = ovl.shape[:3]
        newShape  = dlg.GetShape()
        resampled = ovl.resample(newShape, order=1)

        scale     = [os / float(ns) for os, ns in zip(oldShape, newShape)]
        offset    = [(s - 1) / 2.0  for s in scale]
        scale     = transform.scaleOffsetXform(scale, offset)
        xform     = transform.concat(ovl.voxToWorldMat, scale)
        resampled = fslimage.Image(resampled, xform=xform)

        self.__overlayList.append(resampled)


# TODO Interpolation option

class ResampleDialog(wx.Dialog):

    def __init__(self,
                 parent,
                 title,
                 shape,
                 pixdim):

        wx.Dialog.__init__(self,
                           parent,
                           title=title,
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.__oldShape  = tuple(shape)
        self.__oldPixdim = tuple(pixdim)
        self.__ok     = wx.Button(self, label='Ok',     id=wx.ID_OK)
        self.__cancel = wx.Button(self, label='Cancel', id=wx.ID_CANCEL)

        voxargs = {'minValue'  : 1,
                   'maxValue'  : 9999,
                   'increment' : 1,
                   'width'     : 6,
                   'style'     : floatspin.FSC_INTEGER}

        strvox = ['{:0.2f}'.format(p) for p in shape]
        strpix = ['{:0.2f}'.format(p) for p in pixdim]

        self.__origVoxx    = wx.StaticText(self, label=strvox[0])
        self.__origVoxy    = wx.StaticText(self, label=strvox[1])
        self.__origVoxz    = wx.StaticText(self, label=strvox[2])
        self.__origPixdimx = wx.StaticText(self, label=strpix[0])
        self.__origPixdimy = wx.StaticText(self, label=strpix[1])
        self.__origPixdimz = wx.StaticText(self, label=strpix[2])

        self.__voxx = floatspin.FloatSpinCtrl(self, value=shape[0], **voxargs)
        self.__voxy = floatspin.FloatSpinCtrl(self, value=shape[1], **voxargs)
        self.__voxz = floatspin.FloatSpinCtrl(self, value=shape[2], **voxargs)
        self.__pixdimx = wx.StaticText(self, label=strpix[0])
        self.__pixdimy = wx.StaticText(self, label=strpix[1])
        self.__pixdimz = wx.StaticText(self, label=strpix[2])

        self.__origVoxSizer    = wx.BoxSizer(wx.VERTICAL)
        self.__origPixdimSizer = wx.BoxSizer(wx.VERTICAL)
        self.__voxSizer        = wx.BoxSizer(wx.VERTICAL)
        self.__pixdimSizer     = wx.BoxSizer(wx.VERTICAL)
        self.__origVoxSizer   .Add(self.__origVoxx)
        self.__origVoxSizer   .Add(self.__origVoxy)
        self.__origVoxSizer   .Add(self.__origVoxz)
        self.__origPixdimSizer.Add(self.__origPixdimx)
        self.__origPixdimSizer.Add(self.__origPixdimy)
        self.__origPixdimSizer.Add(self.__origPixdimz)

        self.__voxSizer       .Add(self.__voxx)
        self.__voxSizer       .Add(self.__voxy)
        self.__voxSizer       .Add(self.__voxz)
        self.__pixdimSizer    .Add(self.__pixdimx)
        self.__pixdimSizer    .Add(self.__pixdimy)
        self.__pixdimSizer    .Add(self.__pixdimz)

        self.__dimSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__dimSizer.Add(self.__origVoxSizer)
        self.__dimSizer.Add(self.__origPixdimSizer)
        self.__dimSizer.Add(self.__voxSizer)
        self.__dimSizer.Add(self.__pixdimSizer)

        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__btnSizer.Add(self.__ok,     flag=wx.EXPAND)
        self.__btnSizer.Add(self.__cancel, flag=wx.EXPAND)

        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__mainSizer.Add(self.__dimSizer)
        self.__mainSizer.Add(self.__btnSizer)

        self.SetSizer(self.__mainSizer)

        self.__ok    .Bind(wx.EVT_BUTTON,           self.__onOk)
        self.__cancel.Bind(wx.EVT_BUTTON,           self.__onCancel)
        self.__voxx  .Bind(floatspin.EVT_FLOATSPIN, self.__onVoxel)
        self.__voxy  .Bind(floatspin.EVT_FLOATSPIN, self.__onVoxel)
        self.__voxz  .Bind(floatspin.EVT_FLOATSPIN, self.__onVoxel)

        self.__ok.SetDefault()


    def __onVoxel(self, ev):

        newpix = self.GetPixdim()

        self.__pixdimx.SetLabel('{:0.2f}'.format(newpix[0]))
        self.__pixdimy.SetLabel('{:0.2f}'.format(newpix[1]))
        self.__pixdimz.SetLabel('{:0.2f}'.format(newpix[2]))


    def __onOk(self, ev):
        """Called when the ok button is pushed. """
        self.__newShape = (self.__voxx.GetValue(),
                           self.__voxy.GetValue(),
                           self.__voxz.GetValue())
        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the cancel button is pushed. """
        self.EndModal(wx.ID_CANCEL)


    def GetShape(self):
        return (self.__voxx.GetValue(),
                self.__voxy.GetValue(),
                self.__voxz.GetValue())


    def GetPixdim(self):
        """
        """
        olds = self.__oldShape
        oldp = self.__oldPixdim
        news = self.GetShape()

        pfac = [o / float(n) for o, n in zip(olds, news)]
        newp = [p * f for p, f in zip(oldp, pfac)]

        return newp
