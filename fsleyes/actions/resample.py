#!/usr/bin/env python
#
# resample.py - The ResampleAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ResampleAction` class, a FSLeyes action
which allows the user to resample an image to a different resolution.
"""

import collections

import          wx
import numpy as np

import fsleyes_widgets.floatspin as floatspin
import fsl.data.image            as fslimage
import fsl.utils.image.resample  as resample
import fsleyes.strings           as strings
import fsleyes.tooltips          as tooltips
from . import                       base


class ResampleAction(base.Action):
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``ResampleAction``.

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
        """Called when this ``ResampleAction`` is invoked. Shows a
        ``ResampleDialog``, and then resamples the currently selected overlay.
        """

        ovl  = self.__displayCtx.getSelectedOverlay()
        opts = self.__displayCtx.getOpts(ovl)

        def refCandidate(o):
            return (isinstance(o, fslimage.Nifti) and
                    (o is not ovl)                and
                    not o.sameSpace(ovl))

        refs = [o for o in self.__overlayList if refCandidate(o)]
        dlg  = ResampleDialog(
            self.__frame,
            title=ovl.name,
            shape=ovl.shape,
            pixdim=ovl.pixdim,
            refs=refs)

        if dlg.ShowModal() != wx.ID_OK:
            return

        newShape  = dlg.GetVoxels()
        interp    = dlg.GetInterpolation()
        origin    = dlg.GetOrigin()
        dtype     = dlg.GetDataType()
        smoothing = dlg.GetSmoothing()
        ref       = dlg.GetReference()
        allvols   = dlg.GetAllVolumes()
        interp    = {'nearest' : 0, 'linear' : 1, 'cubic' : 3}[interp]
        name      = '{}_resampled'.format(ovl.name)

        if allvols or ovl.ndim == 3: slc = None
        else:                        slc = opts.index()

        if allvols and ovl.ndim > 3:
            newShape = list(newShape) + list(ovl.shape[3:])

        kwargs = dict(sliceobj=slc,
                      dtype=dtype,
                      order=interp,
                      origin=origin,
                      smooth=smoothing)

        if ref is not None:
            resampled, xform = resample.resampleToReference(ovl, ref, **kwargs)
        else:
            resampled, xform = resample.resample(ovl, newShape, **kwargs)

        resampled = fslimage.Image(resampled,
                                   xform=xform,
                                   header=ovl.header,
                                   name=name)

        self.__overlayList.append(resampled)


class ResampleDialog(wx.Dialog):
    """The ``ResampleDialog`` is used by the ``ResampleAction`` to prompt the
    user for a new resampled image shape. It contains controls allowing the
    user to select new voxel and pixdim values, and to select resampling
    options for interpolation, data type, and smoothing.
    """

    def __init__(self, parent, title, shape, pixdim, refs):
        """Create a ``ResampleDialog``.

        :arg parent: ``wx`` parent object
        :arg title:  Dialog title
        :arg shape:  The original image shape (a tuple of integers)
        :arg pixdim: The original image pixdims (a tuple of floats)
        :arg refs:   A sequence of :class:`.Image` objects which can
                     be selected as references.
        """

        wx.Dialog.__init__(self,
                           parent,
                           title=title,
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.__oldShape   = tuple(shape)
        self.__oldPixdim  = tuple(pixdim)
        self.__references = collections.OrderedDict(
            [(strings.labels[self, 'noref'], None)] +
            [(r.name, r) for r in refs])

        self.__ok        = wx.Button(self, id=wx.ID_OK)
        self.__reset     = wx.Button(self)
        self.__cancel    = wx.Button(self, id=wx.ID_CANCEL)

        self.__ok    .SetLabel(strings.labels[self, 'ok'])
        self.__reset .SetLabel(strings.labels[self, 'reset'])
        self.__cancel.SetLabel(strings.labels[self, 'cancel'])

        voxargs = {'minValue'  : 1,
                   'maxValue'  : 9999,
                   'increment' : 1,
                   'width'     : 6}
        pixargs = {'minValue'  : 0.001,
                   'maxValue'  : 50,
                   'increment' : 0.5,
                   'width'     : 6}

        strvox = ['{:d}'   .format(p) for p in shape]
        strpix = ['{:0.2f}'.format(p) for p in pixdim]

        self.__refLabel     = wx.StaticText(self)
        self.__origVoxLabel = wx.StaticText(self)
        self.__origPixLabel = wx.StaticText(self)
        self.__voxLabel     = wx.StaticText(self)
        self.__pixLabel     = wx.StaticText(self)

        self.__refLabel    .SetLabel(strings.labels[self, 'reference'])
        self.__origVoxLabel.SetLabel(strings.labels[self, 'origVoxels'])
        self.__origPixLabel.SetLabel(strings.labels[self, 'origPixdims'])
        self.__voxLabel    .SetLabel(strings.labels[self, 'newVoxels'])
        self.__pixLabel    .SetLabel(strings.labels[self, 'newPixdims'])

        self.__origVoxx = wx.StaticText(self, label=strvox[0])
        self.__origVoxy = wx.StaticText(self, label=strvox[1])
        self.__origVoxz = wx.StaticText(self, label=strvox[2])
        self.__origPixx = wx.StaticText(self, label=strpix[0])
        self.__origPixy = wx.StaticText(self, label=strpix[1])
        self.__origPixz = wx.StaticText(self, label=strpix[2])

        self.__refChoice = wx.Choice(self,
                                     choices=list(self.__references.keys()))
        self.__refChoice.Enable(len(self.__references) > 1)

        self.__voxx = floatspin.FloatSpinCtrl(self, value=shape[ 0], **voxargs)
        self.__voxy = floatspin.FloatSpinCtrl(self, value=shape[ 1], **voxargs)
        self.__voxz = floatspin.FloatSpinCtrl(self, value=shape[ 2], **voxargs)
        self.__pixx = floatspin.FloatSpinCtrl(self, value=pixdim[0], **pixargs)
        self.__pixy = floatspin.FloatSpinCtrl(self, value=pixdim[1], **pixargs)
        self.__pixz = floatspin.FloatSpinCtrl(self, value=pixdim[2], **pixargs)

        self.__originChoices = ['centre', 'corner']
        self.__interpChoices = ['linear', 'nearest', 'cubic']
        self.__dtypeChoices  = [('float',  np.float32),
                                ('uchar',  np.uint8),
                                ('sshort', np.int16),
                                ('sint',   np.int32),
                                ('double', np.float64)]

        self.__originLabels  = [strings.labels[self, c]
                                for c in self.__originChoices]
        self.__interpLabels  = [strings.labels[self, c]
                                for c in self.__interpChoices]
        self.__dtypeLabels   = [strings.labels[self, c[0]]
                                for c in self.__dtypeChoices]

        self.__originLabel = wx.StaticText(self)
        self.__interpLabel = wx.StaticText(self)
        self.__dtypeLabel  = wx.StaticText(self)
        self.__smoothLabel = wx.StaticText(self)
        self.__allVolLabel = wx.StaticText(self)
        self.__origin      = wx.Choice(self, choices=self.__originLabels)
        self.__interp      = wx.Choice(self, choices=self.__interpLabels)
        self.__dtype       = wx.Choice(self, choices=self.__dtypeLabels)
        self.__smooth      = wx.CheckBox(self)
        self.__allVolumes  = wx.CheckBox(self)

        if len(shape) <= 3:
            self.__allVolumes .Disable()
            self.__allVolLabel.Disable()

        self.__origin    .SetSelection(0)
        self.__interp    .SetSelection(0)
        self.__dtype     .SetSelection(0)
        self.__smooth    .SetValue(True)
        self.__allVolumes.SetValue(True)

        self.__originLabel.SetLabel(strings.labels[self, 'origin'])
        self.__interpLabel.SetLabel(strings.labels[self, 'interpolation'])
        self.__dtypeLabel .SetLabel(strings.labels[self, 'dtype'])
        self.__smoothLabel.SetLabel(strings.labels[self, 'smoothing'])
        self.__allVolLabel.SetLabel(strings.labels[self, 'allVolumes'])

        self.__refLabel.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'reference']))
        self.__refChoice.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'reference']))
        self.__originLabel.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'origin']))
        self.__origin.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'origin']))
        self.__interp     .SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'interpolation']))
        self.__interpLabel.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'interpolation']))
        self.__dtype      .SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'dtype']))
        self.__dtypeLabel .SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'dtype']))
        self.__smooth     .SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'smoothing']))
        self.__smoothLabel.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'smoothing']))
        self.__allVolumes .SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'allVolumes']))
        self.__allVolLabel.SetToolTip(
            wx.ToolTip(tooltips.misc[self, 'allVolumes']))

        self.__refSizer    = wx.BoxSizer(wx.HORIZONTAL)
        self.__labelSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__xrowSizer   = wx.BoxSizer(wx.HORIZONTAL)
        self.__yrowSizer   = wx.BoxSizer(wx.HORIZONTAL)
        self.__zrowSizer   = wx.BoxSizer(wx.HORIZONTAL)
        self.__originSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__interpSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__dtypeSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__smoothSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__allVolSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__btnSizer    = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer   = wx.BoxSizer(wx.VERTICAL)

        self.__refSizer.Add((10, 10),         flag=wx.EXPAND)
        self.__refSizer.Add(self.__refLabel,  flag=wx.EXPAND, proportion=1)
        self.__refSizer.Add((10, 10),         flag=wx.EXPAND)
        self.__refSizer.Add(self.__refChoice, flag=wx.EXPAND, proportion=1)
        self.__refSizer.Add((10, 10),         flag=wx.EXPAND)

        self.__labelSizer.Add((10, 10),            flag=wx.EXPAND)
        self.__labelSizer.Add(self.__origVoxLabel, flag=wx.EXPAND,
                              proportion=1)
        self.__labelSizer.Add((10, 10),            flag=wx.EXPAND)
        self.__labelSizer.Add(self.__origPixLabel, flag=wx.EXPAND,
                              proportion=1)
        self.__labelSizer.Add((10, 10),            flag=wx.EXPAND)
        self.__labelSizer.Add(self.__voxLabel,     flag=wx.EXPAND,
                              proportion=1)
        self.__labelSizer.Add((10, 10),            flag=wx.EXPAND)
        self.__labelSizer.Add(self.__pixLabel,     flag=wx.EXPAND,
                              proportion=1)
        self.__labelSizer.Add((10, 10),            flag=wx.EXPAND)

        self.__xrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__xrowSizer.Add(self.__origVoxx, flag=wx.EXPAND, proportion=1)
        self.__xrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__xrowSizer.Add(self.__origPixx, flag=wx.EXPAND, proportion=1)
        self.__xrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__xrowSizer.Add(self.__voxx,     flag=wx.EXPAND, proportion=1)
        self.__xrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__xrowSizer.Add(self.__pixx,     flag=wx.EXPAND, proportion=1)
        self.__xrowSizer.Add((10, 10),        flag=wx.EXPAND)

        self.__yrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__yrowSizer.Add(self.__origVoxy, flag=wx.EXPAND, proportion=1)
        self.__yrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__yrowSizer.Add(self.__origPixy, flag=wx.EXPAND, proportion=1)
        self.__yrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__yrowSizer.Add(self.__voxy,     flag=wx.EXPAND, proportion=1)
        self.__yrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__yrowSizer.Add(self.__pixy,     flag=wx.EXPAND, proportion=1)
        self.__yrowSizer.Add((10, 10),        flag=wx.EXPAND)

        self.__zrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__zrowSizer.Add(self.__origVoxz, flag=wx.EXPAND, proportion=1)
        self.__zrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__zrowSizer.Add(self.__origPixz, flag=wx.EXPAND, proportion=1)
        self.__zrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__zrowSizer.Add(self.__voxz,     flag=wx.EXPAND, proportion=1)
        self.__zrowSizer.Add((10, 10),        flag=wx.EXPAND)
        self.__zrowSizer.Add(self.__pixz,     flag=wx.EXPAND, proportion=1)
        self.__zrowSizer.Add((10, 10),        flag=wx.EXPAND)

        self.__originSizer.Add((50, 1),            flag=wx.EXPAND)
        self.__originSizer.Add(self.__originLabel, flag=wx.EXPAND)
        self.__originSizer.Add((10, 1),            flag=wx.EXPAND)
        self.__originSizer.Add(self.__origin,      flag=wx.EXPAND)
        self.__originSizer.Add((10, 1),            flag=wx.EXPAND,
                               proportion=1)

        self.__interpSizer.Add((50, 1),            flag=wx.EXPAND)
        self.__interpSizer.Add(self.__interpLabel, flag=wx.EXPAND)
        self.__interpSizer.Add((10, 1),            flag=wx.EXPAND)
        self.__interpSizer.Add(self.__interp,      flag=wx.EXPAND)
        self.__interpSizer.Add((10, 1),            flag=wx.EXPAND,
                               proportion=1)

        self.__dtypeSizer.Add((50, 1),           flag=wx.EXPAND)
        self.__dtypeSizer.Add(self.__dtypeLabel, flag=wx.EXPAND)
        self.__dtypeSizer.Add((10, 1),           flag=wx.EXPAND)
        self.__dtypeSizer.Add(self.__dtype,      flag=wx.EXPAND)
        self.__dtypeSizer.Add((10, 1),           flag=wx.EXPAND,
                               proportion=1)

        self.__smoothSizer.Add((50, 1),            flag=wx.EXPAND)
        self.__smoothSizer.Add(self.__smoothLabel, flag=wx.EXPAND)
        self.__smoothSizer.Add((10, 1),            flag=wx.EXPAND)
        self.__smoothSizer.Add(self.__smooth,      flag=wx.EXPAND)
        self.__smoothSizer.Add((10, 1),            flag=wx.EXPAND,
                               proportion=1)

        self.__allVolSizer.Add((50, 1),            flag=wx.EXPAND)
        self.__allVolSizer.Add(self.__allVolLabel, flag=wx.EXPAND)
        self.__allVolSizer.Add((10, 1),            flag=wx.EXPAND)
        self.__allVolSizer.Add(self.__allVolumes,  flag=wx.EXPAND)
        self.__allVolSizer.Add((10, 1),            flag=wx.EXPAND,
                               proportion=1)

        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND, proportion=1)
        self.__btnSizer.Add(self.__ok,     flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND)
        self.__btnSizer.Add(self.__reset,  flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND)
        self.__btnSizer.Add(self.__cancel, flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND, proportion=1)

        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__refSizer,    flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__labelSizer,  flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__xrowSizer,   flag=wx.EXPAND)
        self.__mainSizer.Add(self.__yrowSizer,   flag=wx.EXPAND)
        self.__mainSizer.Add(self.__zrowSizer,   flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__originSizer, flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__interpSizer, flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__dtypeSizer,  flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__smoothSizer, flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__allVolSizer, flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)
        self.__mainSizer.Add(self.__btnSizer,    flag=wx.EXPAND)
        self.__mainSizer.Add((10, 10),           flag=wx.EXPAND)

        self.SetSizer(self.__mainSizer)

        self.__ok       .Bind(wx.EVT_BUTTON,           self.__onOk)
        self.__reset    .Bind(wx.EVT_BUTTON,           self.__onReset)
        self.__cancel   .Bind(wx.EVT_BUTTON,           self.__onCancel)
        self.__refChoice.Bind(wx.EVT_CHOICE,           self.__onRef)
        self.__voxx     .Bind(floatspin.EVT_FLOATSPIN, self.__onVoxel)
        self.__voxy     .Bind(floatspin.EVT_FLOATSPIN, self.__onVoxel)
        self.__voxz     .Bind(floatspin.EVT_FLOATSPIN, self.__onVoxel)
        self.__pixx     .Bind(floatspin.EVT_FLOATSPIN, self.__onPixdim)
        self.__pixy     .Bind(floatspin.EVT_FLOATSPIN, self.__onPixdim)
        self.__pixz     .Bind(floatspin.EVT_FLOATSPIN, self.__onPixdim)

        self.__ok.SetDefault()

        self.Layout()
        self.Fit()
        self.CentreOnParent()


    @property
    def okButton(self):
        """Returns a reference to the OK button. """
        return self.__ok


    @property
    def resetButton(self):
        """Returns a reference to the reset button. """
        return self.__reset


    @property
    def cancelButton(self):
        """Returns a reference to the cancel button. """
        return self.__cancel


    @property
    def refCtrl(self):
        """Returns a reference to the reference image dropdown. """
        return self.__refChoice


    @property
    def voxXCtrl(self):
        """Returns a reference to the X voxel coordinate spin control. """
        return self.__voxx


    @property
    def voxYCtrl(self):
        """Returns a reference to the Y voxel coordinate spin control. """
        return self.__voxy


    @property
    def voxZCtrl(self):
        """Returns a reference to the Z voxel coordinate spin control. """
        return self.__voxz


    @property
    def pixXCtrl(self):
        """Returns a reference to the X pixdim spin control. """
        return self.__pixx


    @property
    def pixYCtrl(self):
        """Returns a reference to the Y pixdim spin control. """
        return self.__pixy


    @property
    def pixZCtrl(self):
        """Returns a reference to the Z pixdim spin control. """
        return self.__pixz


    @property
    def originCtrl(self):
        """Returns a reference to the origin dropdown box. """
        return self.__origin


    @property
    def interpCtrl(self):
        """Returns a reference to the interpolation dropdown box. """
        return self.__interp


    @property
    def dtypeCtrl(self):
        """Returns a reference to the data type dropdown box. """
        return self.__dtype


    @property
    def smoothCtrl(self):
        """Returns a reference to the smoothing checkbox. """
        return self.__smooth


    @property
    def allVolumesCtrl(self):
        """Returns a reference to the all volumes checkbox. """
        return self.__allVolumes


    def __onRef(self, ev):
        """Called when the user changes the reference image. Enables/
        disables the voxel/pixdim controls as needed.
        """
        ref   = self.__refChoice.GetSelection()
        ref   = self.__refChoice.GetString(ref)
        ref   = self.__references[ref]
        noref = ref is None

        self.__voxx  .Enable(noref)
        self.__voxy  .Enable(noref)
        self.__voxz  .Enable(noref)
        self.__pixx  .Enable(noref)
        self.__pixy  .Enable(noref)
        self.__pixz  .Enable(noref)
        self.__origin.Enable(noref)


    def __onVoxel(self, ev):
        """Called when the user changes a voxel value. Updates the pixdim
        values accordingly.
        """

        newpix = self.__derivePixdims()

        self.__pixx.SetValue(newpix[0])
        self.__pixy.SetValue(newpix[1])
        self.__pixz.SetValue(newpix[2])


    def __onPixdim(self, ev):
        """Called when the user changes a pixdim value. Updates the voxel
        values accordingly.
        """

        newvox = self.__deriveVoxels()

        self.__voxx.SetValue(newvox[0])
        self.__voxy.SetValue(newvox[1])
        self.__voxz.SetValue(newvox[2])


    def __onOk(self, ev):
        """Called when the ok button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_OK)


    def __onReset(self, ev):
        """Called when the reset button is pushed. Resets the shape and pixdims
        to their original values.
        """
        self.__voxx.SetValue(self.__oldShape[ 0])
        self.__voxy.SetValue(self.__oldShape[ 1])
        self.__voxz.SetValue(self.__oldShape[ 2])
        self.__pixx.SetValue(self.__oldPixdim[0])
        self.__pixy.SetValue(self.__oldPixdim[1])
        self.__pixz.SetValue(self.__oldPixdim[2])

        self.__interp.SetSelection(0)
        self.__dtype .SetSelection(0)


    def __onCancel(self, ev):
        """Called when the cancel button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_CANCEL)


    def GetVoxels(self):
        """Returns the current voxel values. """
        return (self.__voxx.GetValue(),
                self.__voxy.GetValue(),
                self.__voxz.GetValue())


    def GetInterpolation(self):
        """Returns the currently selected interpolation setting, either
        ``'nearest'``, ``'linear'``, or ``'cubic'``.
        """
        choice = self.__interp.GetSelection()
        return self.__interpChoices[choice]


    def GetOrigin(self):
        """Returns the currently selected origin setting, either
        ``'corner'``, or ``'centre'``.
        """
        choice = self.__origin.GetSelection()
        return self.__originChoices[choice]


    def GetDataType(self):
        """Returns the currently selected data type setting as a
        ``numpy.dtype``, one of ``uint8``, ``int16``, ``int32``, ``float32``,
        or ``float64``.
        """
        choice = self.__dtype.GetSelection()
        return self.__dtypeChoices[choice][1]


    def GetSmoothing(self):
        """Returns the currently selected smoothing setting, either
        ``True``, or ``False``.
        """
        return self.__smooth.GetValue()


    def GetAllVolumes(self):
        """Returns ``True``, or ``False``, indicating whether all
        volumes of an image with more than three dimensions should be
        resampled.
        """
        return self.__allVolumes.GetValue()


    def GetPixdims(self):
        """Returns the current pixdim values. """
        return (self.__pixx.GetValue(),
                self.__pixy.GetValue(),
                self.__pixz.GetValue())


    def GetReference(self):
        """Return the current reference image value. """
        ref = self.__refChoice.GetSelection()
        ref = self.__refChoice.GetString(ref)
        return self.__references[ref]


    def __derivePixdims(self):
        """Derives new pixdim values from the current voxel values. """
        olds = self.__oldShape
        oldp = self.__oldPixdim
        news = self.GetVoxels()
        fac  = [o / float(n) for o, n in zip(olds, news)]
        newp = [p * f        for p, f in zip(oldp, fac)]

        return newp


    def __deriveVoxels(self):
        """Derives new voxel values from the current pixdim values. """
        olds = self.__oldShape
        oldp = self.__oldPixdim
        newp = self.GetPixdims()
        fac  = [o / float(n) for o, n in zip(oldp, newp)]
        news = [p * f        for p, f in zip(olds, fac)]

        return news
