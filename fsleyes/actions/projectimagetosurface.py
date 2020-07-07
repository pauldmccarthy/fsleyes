#!/usr/bin/env python
#
# projectimagetosurface.py - the ProjectImageToSurfaceAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ProjectImageToSurfaceAction` class,
which allows data from an :class:`.Image` overlay to be projected onto
a :class:`.Mesh` overlay.
"""

import                  wx
import numpy         as np
import scipy.ndimage as ndi

import fsl.transform.affine as affine
import fsl.data.mesh        as fslmesh
import fsl.data.image       as fslimage
import fsleyes.strings      as strings
from . import                  base


class ProjectImageToSurfaceAction(base.NeedOverlayAction):
    """The ``ProjectImageToSurfaceAction`` class allows the user to project
    data from a volumetric :class:`.Image` overlay onto a :class:`.Mesh`
    overlay.

    A ``ProjectImageToSurfaceAction`` is active when the currently selected
    overlay is a :class:`.Mesh`. When executed, the user is prompted to
    select an :class:`.Image` overlay to project onto the mesh. Only images
    which overlap the bounding box of the ``Mesh`` are available as options.

    When the user selects an :class:`.Image`, the data from the image at each
    vertex in the mesh is retrieved using ``scipy.ndimage.map_coordinates``.
    This data is then added as an option on the :attr:`.MeshOpts.vertexData`
    property, and selected.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``ProjectImageToSurfaceAction``.

        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext`
        :arg frame:       The :class:`.ViewPanel` this action is associated
                          with.
        """
        super().__init__(overlayList,
                         displayCtx,
                         self.__projectImage,
                         fslmesh.Mesh)
        self.__frame = frame


    def __projectImage(self):
        """Run the ``ProjectImageToSurfaceAction``. """

        # TODO Allow user to load an image from file?


        # We need to use child DisplayOpts objects in
        # order to perform the projection, as the parent
        # DisplayOpts objects do not maintain information
        # about transformations between the different
        # coordinate systems. Any child DisplayContext
        # will do.
        displayCtx = self.__frame.viewPanels[0].displayCtx
        mesh       = self.displayCtx.getSelectedOverlay()
        mopts      = displayCtx.getOpts(mesh)

        # any images which overlap with the
        # mesh bbox in the display coordinate
        # system are given as options
        images = []
        mbbox  = affine.transform(
            mesh.bounds, mopts.getTransform('mesh', 'display'))
        mbbox  = list(zip(*mbbox))

        for o in self.overlayList:

            if not isinstance(o, fslimage.Image):
                continue

            iopts = displayCtx.getOpts(o)
            ibbox = affine.axisBounds(
                o.shape[:3], iopts.getTransform('voxel', 'display'))
            ibbox = list(zip(*ibbox))

            if overlap(mbbox, ibbox):
                images.append(o)

        # can't find any images which
        # overlap with the mesh in the
        # display coordinate system
        if len(images) == 0:
            wx.MessageDialog(
                self.__frame,
                message=strings.messages[self, 'noOverlap'],
                style=(wx.ICON_EXCLAMATION | wx.OK)).ShowModal()
            return

        # ask the user what image
        # they want to project
        dlg = ProjectImageDialog(self.__frame, images)
        if dlg.ShowModal() != wx.ID_OK:
            return

        # transform the mesh vertices
        # into  the voxel coordinate
        # system of the selected image
        image   = dlg.GetImage()
        iopts   = displayCtx.getOpts(image)
        m2d     = mopts.getTransform('mesh', 'display')
        verts   = mesh.vertices
        verts   = iopts.transformCoords(verts, 'display', 'voxel', pre=m2d)

        # sample the image data at
        # every vertex location
        imgdata = image.data[iopts.index()]
        vdata   = ndi.map_coordinates(imgdata, verts.T)

        # add the vertex data to
        # the mesh, and select it
        key              = mopts.addVertexData(image.name, vdata)
        mopts.vertexData = key


class ProjectImageDialog(wx.Dialog):
    """A dialog which prompts the user to select an image to project. """


    def __init__(self, parent, images):
        """Create a ``ProjectImageDialog``.

        :arg parent: ``wx`` parent object
        :arg images: sequence of :class:`.Image` overlays
        """
        wx.Dialog.__init__(self,
                           parent,
                           title=strings.titles[self],
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.__images = list(images)
        imageNames    = [i.name for i in images]

        self.__ok          = wx.Button(self, id=wx.ID_OK)
        self.__cancel      = wx.Button(self, id=wx.ID_CANCEL)
        self.__label       = wx.StaticText(self)
        self.__imageChoice = wx.Choice(self, choices=imageNames)

        self.__ok    .SetLabel(strings.labels[self, 'ok'])
        self.__cancel.SetLabel(strings.labels[self, 'cancel'])
        self.__label .SetLabel(strings.labels[self, 'message'])

        self.__imageChoice.SetSelection(0)

        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer  = wx.BoxSizer(wx.HORIZONTAL)

        self.__btnSizer.Add(self.__ok,
                            border=5,
                            proportion=1,
                            flag=wx.EXPAND | wx.ALL)
        self.__btnSizer.Add(self.__cancel,
                            border=5,
                            proportion=1,
                            flag=wx.EXPAND | wx.ALL)

        self.__mainSizer.Add(self.__label,
                             border=10,
                             proportion=1,
                             flag=wx.EXPAND | wx.ALL)
        self.__mainSizer.Add(self.__imageChoice,
                             border=5,
                             proportion=1,
                             flag=wx.EXPAND | wx.ALL)
        self.__mainSizer.Add(self.__btnSizer,
                             border=5,
                             proportion=1,
                             flag=wx.EXPAND | wx.ALL)

        self.SetSizer(self.__mainSizer)

        self.__ok    .Bind(wx.EVT_BUTTON, self.__onOk)
        self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)

        self.__ok.SetDefault()

        self.Layout()
        self.Fit()
        self.CentreOnParent()


    def GetImage(self):
        """Returns the selected image."""
        return self.__images[self.__imageChoice.GetSelection()]


    def __onOk(self, ev):
        """Called when the ok button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the cancel button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_CANCEL)


def overlap(bbox1, bbox2):
    """Returns ``True`` if the two bounding boxes overlap at all, ``False``
    otherwise.

    Both ``bbox1`` and ``bbox2`` are expected to be sequences of
    ``(low, high)`` tuples containing the bounds of each axis in the
    coordinate system that the bounding boxes are defined in.
    """

    def axisOverlap(lo1, hi1, lo2, hi2):
        return (hi1 >= lo2) and (lo1 <= hi2) or \
               (hi2 >= lo1) and (lo2 <= hi1)

    for (lo1, hi1), (lo2, hi2) in zip(bbox1, bbox2):
        if not axisOverlap(lo1, hi1, lo2, hi2):
            return False

    return True
