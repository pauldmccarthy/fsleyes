#!/usr/bin/env python
#
# loadvertexdata.py - The LoadVertexDataAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadVertexDataAction`, which allows the
user to load additional vertex data or vertex sets for a :class:`.Mesh`
overlay. Two standalone functions, :func:`loadVertexData` and
:func:`loadVertices` are also provided.
"""


import os.path as op

import fsl.data.mesh                as fslmesh
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
from . import                          base


class LoadVertexDataAction(base.Action):
    """The ``LoadVertexDataAction`` prompts the user to load a file containing
    vertex data or a vertex set for a :class:`.Mesh` overlay.  See the
    :attr:`.MeshOpts.vertexData` and :attr:`.MeshOpts.vertexSet` properties.
    """


    def __init__(self, overlayList, displayCtx, vertices=False):
        """Create a ``LoadVertexDataAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg vertices:    If ``True``, the user is prompted to load a file
                          containing vertices for the mesh. Otherwise, the user
                          is prompted to load a file containing vertex data.
        """
        base.Action.__init__(self, self.__onRun)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__vertices    = vertices
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

        self.enabled = isinstance(overlay, fslmesh.Mesh)


    def __onRun(self):
        """Called when this action is executed.  Calls either
        :meth:`__loadVertexData`, or :meth:`__loadVertices`.
        """
        if self.__vertices: self.__loadVertices()
        else:               self.__loadVertexData()


    def __loadVertices(self):
        """Prompts the user to load a vertex file for the currently
        selected :class:`.Mesh` overlay, then sets the
        :attr:`.MeshOpts.vertexSet` property accordingly. If the file was
        successfully loaded, also adds the loaded file as an option on the
        :attr:`.MeshOpts.vertexSet` property.
        """
        self.__loadit('loadVertices', loadVertices)


    def __loadVertexData(self):
        """Prompts the user to load a vertex data file for the currently
        selected :class:`.Mesh` overlay, then sets the
        :attr:`.MeshOpts.vertexData` property accordingly. If the file was
        successfully loaded, also adds the loaded file as an option on the
        :attr:`.MeshOpts.vertexData` property.
        """
        self.__loadit('loadVertexData', loadVertexData)


    def __loadit(self, key, func):
        """Shared by the :meth:`__loadVertices` and :meth:`__loadVertexData`
        methods.
        """

        import wx

        app     = wx.GetApp()
        overlay = self.__displayCtx.getSelectedOverlay()
        fromDir = op.dirname(overlay.dataSource)

        msg = strings.messages[self, key].format(overlay.name)
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

        with status.reportIfError(errtitle, errmsg, raiseError=False):
            func(overlay, self.__displayCtx, path)


def loadVertexData(overlay, displayCtx, filename, select=True):
    """Attempt to load the specified vertex data for the given overlay.

    :arg overlay:    The overlay (assumed to be a :class:`.Mesh` instance)

    :arg displayCtx: The :class:`.DisplayContext`

    :arg filename:   Path to the vertex data file that is to be loaded, or key
                     for vertex data that is already loaded (see the
                     :class:`.Mesh` class).

    :arg select:     If ``True`` (the default), the
                     :attr:`.MeshOpts.vertexData` is set to the
                     newly loaded file.

    :returns:        The path that was actually used - it will have been
                     converted to an absolute path if necessary.
    """

    opts     = displayCtx.getOpts(overlay)
    filename = op.abspath(filename)

    # The sole reason that this function exists is because
    # MeshOpts.vertexData is a props.Choice property, which
    # can only take one of a fixed set of values. So when
    # we want to load some data from a file that is not in
    # the possible values, we need to add the file as an
    # option before selecting it. A bit silly.
    if filename not in overlay.vertexDataSets():
        # Force the overlay to load
        # the vertex data. This will
        # throw an error if the file
        # is unrecognised.
        overlay.loadVertexData(filename)

        # Add the file as an
        # option, then select it.
        opts.addVertexDataOptions([filename])

    if select:
        opts.vertexData = filename

    return filename


def loadVertices(overlay, displayCtx, filename, select=True):
    """Attempt to load the specified vertexz file for the given overlay.

    :arg overlay:    The overlay (assumed to be a :class:`.Mesh` instance)

    :arg displayCtx: The :class:`.DisplayContext`

    :arg filename:   Path to the vertex file that is to be loaded, or key
                     for vertex data that is already loaded (see the
                     :class:`.Mesh` class).

    :arg select:     If ``True`` (the default), the
                     :attr:`.MeshOpts.vertexSet` is set to the
                     newly loaded file.

    :returns:        The path that was actually used - it will have been
                     converted to an absolute path if necessary.
    """

    opts     = displayCtx.getOpts(overlay)
    filename = op.abspath(filename)

    # We follow the same process
    # as in loadVertexData above
    if filename not in overlay.vertexSets():
        overlay.loadVertices(filename, select=False)
        opts.addVertexSetOptions([filename])

    if select:
        overlay.vertices = filename

    return filename
