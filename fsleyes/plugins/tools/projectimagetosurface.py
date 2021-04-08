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
import fsleyes.actions.base as base


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
        displayCtx = self.__frame.focusedViewPanel.displayCtx
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
        dlg = wx.SingleChoiceDialog(
            self.__frame,
            caption=strings.titles[self, 'dialog'],
            message=strings.labels[self, 'message'],
            style=wx.OK | wx.CANCEL,
            choices=[i.name for i in images])

        if dlg.ShowModal() != wx.ID_OK:
            return

        # Sample data from the selected image
        image = images[dlg.GetSelection()]
        vdata = projectImageDataOntoMesh(displayCtx, image, mesh)

        # add the vertex data to
        # the mesh, and select it
        key              = mopts.addVertexData(image.name, vdata)
        mopts.vertexData = key


def projectImageDataOntoMesh(displayCtx, image, mesh):
    """Samples data from ``image`` at every vertex on ``mesh``. Uses
    ``scipy.ndimage.map_coordinates``.
    """

    # transform the mesh vertices into
    # the image voxel coordinate system
    mopts   = displayCtx.getOpts(mesh)
    iopts   = displayCtx.getOpts(image)
    m2d     = mopts.getTransform('mesh', 'display')
    verts   = mesh.vertices
    verts   = iopts.transformCoords(verts, 'display', 'voxel', pre=m2d)

    # sample the image data at
    # every vertex location
    imgdata = image.data[iopts.index()]
    vdata   = ndi.map_coordinates(imgdata,
                                  verts.T,
                                  output=np.float64,
                                  cval=np.nan)

    return vdata


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
