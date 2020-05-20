#!/usr/bin/env python
#
# newimage.py - The NewImageAction class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`NewImageAction` class, an :class:`.Action`
which allows the user to create a new empty :class:`.Image` overlay.
"""


import            wx
import wx.grid as wxgrid

import numpy   as np
import nibabel as nib

import fsl.transform.affine      as fslaffine
import fsl.data.constants        as constants
import fsl.data.image            as fslimage
import fsleyes_widgets.floatspin as floatspin
import fsleyes.strings           as strings
from . import                       base


class NewImageAction(base.Action):
    """The ``NewImageAction`` class allows the user to create a new
    :class:`.Image`.  When invoked, it displays a :class:`NewImageDialog`
    prompting the user to select the properties of the new image, and then
    creates a new image accordingly.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``CopyOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, overlayList, displayCtx, self.__newImage)
        self.__frame = frame


    def __newImage(self):
        """Displays a :class:`NewImageDialog`, then creates a new
        :class:`.Image`, and adds it to the :class:`.OverlayList`.

        If the currently selected overlay is a :class:`.Nifti`, the
        :class:`NewImageDialog` is initialised to the properties of
        the selected overlay.
        """

        ovl = self.displayCtx.getSelectedOverlay()

        if ovl is not None and isinstance(ovl, fslimage.Nifti):
            shape     = ovl.shape[:3]
            pixdim    = ovl.pixdim[:3]
            dtype     = ovl.dtype
            affine    = ovl.voxToWorldMat
            xyzUnits  = ovl.xyzUnits
            timeUnits = ovl.timeUnits

            # adjust pixdims in case there
            # are inversions (e.g. l/r flip)
            pixdim = pixdim * np.sign(fslaffine.decompose(affine)[0])
        else:
            shape     = None
            pixdim    = None
            dtype     = None
            affine    = np.eye(4)
            xyzUnits  = None
            timeUnits = None

        dlg = NewImageDialog(self.__frame,
                             shape=shape,
                             pixdim=pixdim,
                             affine=affine,
                             dtype=dtype)

        if dlg.ShowModal() != wx.ID_OK:
            return

        img = newImage(dlg.shape,
                       dlg.pixdim,
                       dlg.dtype,
                       dlg.affine,
                       xyzUnits=xyzUnits,
                       timeUnits=timeUnits,
                       name='new')
        self.overlayList.append(img)
        self.displayCtx.selectOverlay(img)


def newImage(shape,
             pixdim,
             dtype,
             affine,
             xyzUnits=constants.NIFTI_UNITS_MM,
             timeUnits=constants.NIFTI_UNITS_SEC,
             name='new'):
    """Create a new :class:`.Image` with the specified properties.

    :arg shape:      Tuple containing the image shape
    :arg pixdim:     Tuple containing the image pixdims
    :arg dtype:      ``numpy`` ``dtype``
    :arg affine:     ``(4, 4)`` ``numpy`` array specifying the voxel-to-world
                     affine
    :arg xyzUnits:   Spatial units
    :arg timeUnits:  Temporal units
    """
    data = np.zeros(shape, dtype=dtype)
    img  = nib.Nifti2Image(data, affine)
    img.header.set_zooms(np.abs(pixdim))
    img.header.set_xyzt_units(xyzUnits, timeUnits)
    return fslimage.Image(img, name=name)


class NewImageDialog(wx.Dialog):
    """The ``NewImageDialog`` displays a collection of widgets allowing the
    user to select the data type, shape, dimensions (pixdims), and voxel-to-
    world affine.
    """

    def __init__(self, parent, shape, pixdim, affine, dtype):
        """Create a ``NewImageDialog``.

        :arg parent: ``wx`` parent object
        :arg shape:  Tuple of three initial shape values
        :arg pixdim: Tuple of three initial pixdim values
        :arg affine: Initial affine, assumed to be a ``(4, 4)`` ``numpy``
                     array
        :arg dtype:  Initial ``numpy`` dtype. Must be one of ``float32``,
                     ``float64``, ``uint8``, ``int16``, or ``int32``.
        """

        if shape  is None: shape  = (100, 100, 100)
        if pixdim is None: pixdim = (1, 1, 1)
        if affine is None: affine = np.eye(4)
        if dtype  is None: dtype  = np.float32

        dtypeLabels = ['float',    'uchar',  'sshort', 'sint',   'double']
        dtypeValues = [np.float32, np.uint8, np.int16, np.int32, np.float64]
        dtypeLabels = [strings.labels[self, l] for l in dtypeLabels]

        if dtype in dtypeValues: dtype = dtypeValues.index(dtype)
        else:                    dtype = 0

        self.__dtypeValues = dtypeValues

        wx.Dialog.__init__(self,
                           parent,
                           title=strings.titles[self],
                           style=wx.DEFAULT_DIALOG_STYLE)

        dtypeLabel  = strings.labels[self, 'dtype']
        shapeLabel  = strings.labels[self, 'shape']
        pixdimLabel = strings.labels[self, 'pixdim']
        affineLabel = strings.labels[self, 'affine']
        linkLabel   = strings.labels[self, 'link']
        okLabel     = strings.labels[self, 'ok']
        cancelLabel = strings.labels[self, 'cancel']

        self.__dtypeLabel  = wx.StaticText(self, label=dtypeLabel)
        self.__shapeLabel  = wx.StaticText(self, label=shapeLabel)
        self.__pixdimLabel = wx.StaticText(self, label=pixdimLabel)
        self.__affineLabel = wx.StaticText(self, label=affineLabel)
        self.__xLabel      = wx.StaticText(self, label='X')
        self.__yLabel      = wx.StaticText(self, label='Y')
        self.__zLabel      = wx.StaticText(self, label='Z')
        self.__dtype       = wx.Choice(self, choices=dtypeLabels)
        self.__ok          = wx.Button(self, id=wx.ID_OK,     label=okLabel)
        self.__cancel      = wx.Button(self, id=wx.ID_CANCEL, label=cancelLabel)

        self.__dtype.SetSelection(dtype)

        shapewidgets  = []
        pixdimwidgets = []

        for i in range(3):
            shapew  = floatspin.FloatSpinCtrl(self,
                                              minValue=1,
                                              maxValue=2 ** 64 - 1,
                                              increment=1,
                                              value=shape[i],
                                              style=floatspin.FSC_INTEGER)
            pixdimw = floatspin.FloatSpinCtrl(self,
                                              minValue=-100,
                                              maxValue=100,
                                              increment=0.5,
                                              value=pixdim[i])

            shapewidgets .append(shapew)
            pixdimwidgets.append(pixdimw)

        self.__shapex  = shapewidgets[ 0]
        self.__shapey  = shapewidgets[ 1]
        self.__shapez  = shapewidgets[ 2]
        self.__pixdimx = pixdimwidgets[0]
        self.__pixdimy = pixdimwidgets[1]
        self.__pixdimz = pixdimwidgets[2]
        self.__link    = wx.CheckBox(self, label=linkLabel)
        self.__link.SetValue(True)

        self.__affine = wxgrid.Grid(self)
        self.__affine.SetDefaultEditor(wxgrid.GridCellFloatEditor(-1, 2))
        self.__affine.CreateGrid(4, 4)
        self.__affine.HideRowLabels()
        self.__affine.HideColLabels()
        for i in range(4):
            self.__affine.SetColFormatFloat(i, -1, 2)
        self.affine = affine

        self.__mainSizer      = wx.BoxSizer(wx.VERTICAL)
        self.__dtypeSizer     = wx.BoxSizer(wx.HORIZONTAL)
        self.__affineSizer    = wx.BoxSizer(wx.HORIZONTAL)
        self.__affineLblSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__shapepixSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__shapepixGrid   = wx.FlexGridSizer(4, 3, 0, 0)
        self.__buttonSizer    = wx.BoxSizer(wx.HORIZONTAL)

        self.__dtypeSizer.Add((1, 1), proportion=1)
        self.__dtypeSizer.Add(self.__dtypeLabel)
        self.__dtypeSizer.Add(self.__dtype)
        self.__dtypeSizer.Add((1, 1), proportion=1)

        self.__shapepixGrid .Add((1, 1))
        self.__shapepixGrid .Add(self.__shapeLabel)
        self.__shapepixGrid .Add(self.__pixdimLabel)
        self.__shapepixGrid .Add(self.__xLabel)
        self.__shapepixGrid .Add(self.__shapex)
        self.__shapepixGrid .Add(self.__pixdimx)
        self.__shapepixGrid .Add(self.__yLabel)
        self.__shapepixGrid .Add(self.__shapey)
        self.__shapepixGrid .Add(self.__pixdimy)
        self.__shapepixGrid .Add(self.__zLabel)
        self.__shapepixGrid .Add(self.__shapez)
        self.__shapepixGrid .Add(self.__pixdimz)
        self.__shapepixSizer.Add((1, 1), proportion=1)
        self.__shapepixSizer.Add(self.__shapepixGrid)
        self.__shapepixSizer.Add((1, 1), proportion=1)

        self.__affineSizer.Add((1, 1), proportion=1)
        self.__affineSizer.Add(self.__affine)
        self.__affineSizer.Add((1, 1), proportion=1)

        self.__affineLblSizer.Add(self.__affineLabel)
        self.__affineLblSizer.Add((10, 1))
        self.__affineLblSizer.Add(self.__link)

        self.__buttonSizer.Add((1, 1), proportion=1)
        self.__buttonSizer.Add(self.__ok)
        self.__buttonSizer.Add(self.__cancel)
        self.__buttonSizer.Add((1, 1), proportion=1)

        szargs = {'flag'   : wx.EXPAND | wx.LEFT | wx.RIGHT,
                  'border' : 5}

        self.__mainSizer.Add((1, 10))
        self.__mainSizer.Add(self.__dtypeSizer, **szargs)
        self.__mainSizer.Add((1, 10))
        self.__mainSizer.Add(self.__shapepixSizer, **szargs)
        self.__mainSizer.Add((1, 10))
        self.__mainSizer.Add(self.__affineLblSizer, **szargs)
        self.__mainSizer.Add((1, 10))
        self.__mainSizer.Add(self.__affineSizer, **szargs)
        self.__mainSizer.Add((1, 10))
        self.__mainSizer.Add(self.__buttonSizer, **szargs)
        self.__mainSizer.Add((1, 10))

        self.SetSizer(self.__mainSizer)
        self.Layout()
        self.Fit()
        self.__ok.SetFocus()

        self.__pixdimx.Bind(floatspin.EVT_FLOATSPIN,      self.__onPixdim)
        self.__pixdimy.Bind(floatspin.EVT_FLOATSPIN,      self.__onPixdim)
        self.__pixdimz.Bind(floatspin.EVT_FLOATSPIN,      self.__onPixdim)
        self.__affine .Bind(wxgrid.EVT_GRID_CELL_CHANGED, self.__onAffine)
        self.__link   .Bind(wx.EVT_CHECKBOX,              self.__onLink)


    def __onLink(self, ev):
        """Called when the link checkbox changes. If linking is enabled,
        calls :meth:`__onAffine`.
        """
        if not self.link:
            return

        # affine takes precedence
        self.__onAffine(ev)



    def __onPixdim(self, ev):
        """Called when any pixdim widget changes. If linking is enabled,
        reconstructs the affine with the new pixdim values.
        """
        if not self.link:
            return

        # If we construct an affine with
        # scales == 0, we get explosions
        if any([p == 0 for p in self.pixdim]):
            return

        offsets, rotations = fslaffine.decompose(self.affine)[1:]
        self.affine = fslaffine.compose(self.pixdim, offsets, rotations)


    def __onAffine(self, ev):
        """Called when the affine changes. If linking is enabled, updates
        the pixdim values from the new affine.
        """
        if not self.link:
            return

        scales = fslaffine.decompose(self.affine)[0]
        self.__pixdimx.SetValue(scales[0])
        self.__pixdimy.SetValue(scales[1])
        self.__pixdimz.SetValue(scales[2])


    @property
    def linkWidget(self):
        """Return a reference to the link widget. """
        return self.__link


    @property
    def shapeWidgets(self):
        """Return a reference to the three shape widgets. """
        return (self.__shapex, self.__shapey, self.__shapez)


    @property
    def pixdimWidgets(self):
        """Return a reference to the three pixdim widgets. """
        return (self.__pixdimx, self.__pixdimy, self.__pixdimz)


    @property
    def dtypeWidget(self):
        """Return a reference to the dtype widget. """
        return self.__dtype


    @property
    def affineWidget(self):
        """Return a reference to the affine widget. """
        return self.__affine


    @property
    def ok(self):
        """Return a reference to the ok button. """
        return self.__ok


    @property
    def cancel(self):
        """Return a reference to the cancel button. """
        return self.__cancel


    @property
    def link(self):
        """Return a tuple containing the current affine-dimension link checkbox
        value.
        """
        return self.__link.GetValue()


    @property
    def shape(self):
        """Return a tuple containing the current shape values. """
        return (self.__shapex.GetValue(),
                self.__shapey.GetValue(),
                self.__shapez.GetValue())


    @property
    def pixdim(self):
        """Return a tuple containing the current pixdim values. """
        return (self.__pixdimx.GetValue(),
                self.__pixdimy.GetValue(),
                self.__pixdimz.GetValue())


    @property
    def dtype(self):
        """Return the currently selected data type, as a ``numpy.dtype``. """
        return self.__dtypeValues[self.__dtype.GetSelection()]


    @property
    def affine(self):
        """Return the current content of the affine grid, as a ``numpy``
        array of shape ``(4, 4)``.
        """
        aff = np.zeros((4, 4), dtype=np.float64)
        for i in range(4):
            for j in range(4):
                aff[i, j] = float(self.__affine.GetCellValue(i, j))
        return aff


    @affine.setter
    def affine(self, aff):
        """Set the current contents of the affine grid to ``aff``, assumed
        to be a ``(4, 4)`` ``numpy`` array.
        """
        for i in range(4):
            for j in range(4):
                val = '{:0.2f}'.format(aff[i, j])
                self.__affine.SetCellValue((i, j), val)
