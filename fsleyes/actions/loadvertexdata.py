#!/usr/bin/env python
#
# loadvertexdata.py - The LoadVertexDataAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadVertexDataAction`, which allows
the user to load vertex data for a :class:`.TriangleMesh` overlay. A
standalone function, :func:`loadVertexData` is also provided.
"""


import os.path          as op

import fsl.data.mesh                as fslmesh
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
from . import                          base


class LoadVertexDataAction(base.Action):
    """The ``LoadVertexDataAction`` prompts the user to load a file
    containing vertex data for a :class:`.TriangleMesh` overlay.
    See the :attr:`.MeshOpts.vertexData` property.
    """


    def __init__(self, overlayList, displayCtx):
        """Create a ``LoadVertexDataAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        base.Action.__init__(self, self.__loadVertexData)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)


    def destroy(self):
        """Must be called when this ``LoadVertexDataAction`` is no longer
        needed. Performs some clean-up.
        """
        self.__displayCtx .removeListener('selectedOverlay', self.__name)
        self.__overlayList.removeListener('overlays',        self.__name)

        base.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Enables/disables this action based on the type of the newly selected
        overlay.
        """

        overlay = self.__displayCtx.getSelectedOverlay()

        self.enabled = isinstance(overlay, fslmesh.TriangleMesh)


    def __loadVertexData(self):
        """Called when this action is executed. Prompts the user to load
        some vertex data for the currently selected :class:`.TriangleMesh`
        overlay, then sets the :attr:`.MeshOpts.vertexData` property
        accordingly. If the file was successfully loaded, also adds the
        loaded file as an option on the :attr:`.MeshOpts.vertexData`
        property.
        """

        import wx

        app     = wx.GetApp()
        overlay = self.__displayCtx.getSelectedOverlay()
        fromDir = op.dirname(overlay.dataSource)

        msg = strings.messages[self, 'loadVertexData'].format(overlay.name)
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message=msg,
                            defaultDir=fromDir,
                            wildcard='*.*',
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        path     = dlg.GetPath()
        errtitle = strings.titles[  self, 'error']
        errmsg   = strings.messages[self, 'error'].format(overlay.name)

        with status.reportIfError(errtitle, errmsg):
            loadVertexData(overlay, self.__displayCtx, path)


def loadVertexData(overlay, displayCtx, filename):
    """Attempt to load the specified vertex data for the given overlay.

    :arg overlay:    The overlay (assumed to be a :class:`.TriangleMesh`
                     instance)

    :arg displayCtx: The :class:`.DisplayContext`

    :arg filename:   Path to the vertex data file that is to be loaded.
    """

    opts = displayCtx.getOpts(overlay)

    # The sole reason that this function exists is because
    # MeshOpts.vertexData is a props.Choice property, which
    # can only take one of a fixed set of values. So when
    # we want to load some data from a file that is not in
    # the possible values, we need to add the file as an
    # option before selecting it. A bit silly.

    # Force the overlay to load
    # the vertex data. This will
    # throw an error if the file
    # is unrecognised.
    overlay.getVertexData(filename)

    # Add the file as an
    # option, then select it.
    opts.addVertexDataOptions([filename])
    opts.vertexData = filename
