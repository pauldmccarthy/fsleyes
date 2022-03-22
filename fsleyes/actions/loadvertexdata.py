#!/usr/bin/env python
#
# loadvertexdata.py - The LoadVertexDataAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadVertexDataAction`, which allows the
user to load additional vertex data, streamline data, or vertex sets for a
:class:`.Mesh` or :class:`.Tractogram` overlay. Three standalone functions,
:func:`loadVertexData`, :func:`loadStreamlineData` and :func:`loadVertices`
are also provided.
"""


import os.path as op

import fsl.data.mesh                as fslmesh
import fsleyes.data.tractogram      as tractogram
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
import fsleyes.actions.base         as base


class LoadVertexDataAction(base.NeedOverlayAction):
    """The ``LoadVertexDataAction`` prompts the user to load a file containing
    vertex or streamline data or a vertex set for a :class:`.Mesh` or
    :class:`.Tractogram` overlay.  See the :attr:`.MeshOpts.vertexData`,
    :attr:`.MeshOpts.vertexSet`, and :attr:`.TractogramOpts.vertexData`
    properties.
    """


    def __init__(self, overlayList, displayCtx, loadWhat, ovlType):
        """Create a ``LoadVertexDataAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.

        :arg loadWhat:    One of ``'vertexData'`` or ``'vertices'``, denoting
                          the type of file that is to be loaded.

        :arg ovlType:     Overlay type - one of :class:`.Mesh` or
                          :class:`.Tractogram`.
        """
        base.NeedOverlayAction.__init__(
            self, overlayList, displayCtx, self.__onRun, ovlType)
        self.__loadWhat = loadWhat


    def __onRun(self):
        """Called when this action is executed.  Calls either
        :meth:`__loadVertexData`, or :meth:`__loadVertices`.
        """
        if   self.__loadWhat == 'vertices':   self.__loadVertices()
        elif self.__loadWhat == 'vertexData': self.__loadVertexData()


    def __loadVertices(self):
        """Prompts the user to load a vertex file for the currently
        selected :class:`.Mesh` overlay, then sets the
        :attr:`.MeshOpts.vertexSet` property accordingly. If the file was
        successfully loaded, also adds the loaded file as an option on the
        :attr:`.MeshOpts.vertexSet` property.
        """
        self.__loadit('loadVertices', loadVertices)


    def __loadVertexData(self):
        """Prompts the user to load a vertex or streamline data file for the
        currently selected :class:`.Mesh` or :class:`.Tractogram` overlay, then
        sets the :attr:`.MeshOpts.vertexData` or
        :attr:`.TractogramOpts.vertexData` property accordingly. If the file
        was successfully loaded, also adds the loaded file as an option on the
        :attr:`.MeshOpts.vertexData` or :attr:`.TractogramOpts.vertexData`
        property.
        """
        self.__loadit('loadVertexData', loadVertexData)


    def __loadit(self, key, func):
        """Shared by the :meth:`__loadVertices`, and :meth:`__loadVertexData`
        methods.
        """

        import wx

        app     = wx.GetApp()
        overlay = self.displayCtx.getSelectedOverlay()
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
            func(overlay, self.displayCtx, path)


def loadVertexData(overlay, displayCtx, filename, select=True):
    """Attempt to load the specified per-vertex/streamline data for the given
    overlay.

    :arg overlay:    The overlay (assumed to be a :class:`.Mesh` or
                     :class:`.Tractogram` instance)

    :arg displayCtx: The :class:`.DisplayContext`

    :arg filename:   Path to the vertex data file that is to be loaded, or key
                     for vertex data that is already loaded (see the
                     :class:`.Mesh` and :class:`.Tractogram` classes).

    :arg select:     If ``True`` (the default), the
                     :attr:`.MeshOpts.vertexData` or
                     :attr:`.TractogramOpts.vertexData` is set to the newly
                     loaded file.

    :returns:        The path that was actually used - it will have been
                     converted to an absolute path if necessary.
    """

    opts     = displayCtx.getOpts(overlay)
    filename = op.abspath(filename)

    # The sole reason that this function exists is because
    # [Mesh|Tractogram]Opts.vertexData is a props.Choice
    # property, which can only take one of a fixed set of
    # values. So when we want to load some data from a
    # file that is not in the possible values, we need to
    # add the file as an option before selecting it. A bit
    # silly.
    if filename not in overlay.vertexDataSets():
        # Force the overlay to load
        # the vertex data. This will
        # throw an error if the file
        # is unrecognised.
        overlay.loadVertexData(filename)

        # Add the file as an option to the
        # MeshOpts/TractogramOpts instance
        if isinstance(overlay, fslmesh.Mesh):
            opts.addVertexDataOptions([filename])
        else:
            opts.updateColourClipModes()

    if select:
        if isinstance(overlay, fslmesh.Mesh):
            opts.vertexData = filename
        else:
            opts.colourMode = filename

    return filename


def loadVertices(overlay, displayCtx, filename, select=True):
    """Attempt to load the specified vertex file for the given overlay.

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
