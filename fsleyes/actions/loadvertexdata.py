#!/usr/bin/env python
#
# loadvertexdata.py - The LoadVertexDataAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadVertexDataAction`, which allows
the user to load vertex data for a :class:`.TriangleMesh` overlay.
"""


import os.path         as op

import fsl.data.mesh   as fslmesh

import fsleyes.strings as strings
from . import             action


class LoadVertexDataAction(action.Action):
    """The ``LoadVertexDataAction`` prompts the user to load a file
    containing vertex data for a :class:`.TriangleMesh` overlay.
    See the :attr:`.MeshOpts.vertexData` property.
    """

    
    def __init__(self, overlayList, displayCtx):
        """Create a ``LoadVertexDataAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """ 
        action.Action.__init__(self, self.__loadVertexData)

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

        action.Action.destroy(self)


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
        opts    = self.__displayCtx.getOpts(overlay)
        fromDir = op.dirname(overlay.dataSource)

        msg = strings.messages[self, 'loadVertexData'].format(overlay.name)
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message=msg,
                            defaultDir=fromDir,
                            wildcard='*.*',
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        path = dlg.GetPath()

        try:

            # Force the overlay to
            # load the vertex data
            overlay.getVertexData(path)
            opts.addVertexDataOptions([path])
            opts.vertexData = path
            
        except Exception as e:

            msg = strings.messages[self, 'error']
            msg = msg.format(overlay.name, str(e))

            wx.MessageDialog(
                app.GetTopWindow(),
                message=msg,
                style=wx.ICON_ERROR).ShowModal() 
