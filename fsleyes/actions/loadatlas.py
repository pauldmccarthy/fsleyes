#!/usr/bin/env python
#
# loadatlas.py - The LoadAtlas action.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadAtlasAction`, an action which
allows the user to load an atlas specification into FSLeyes. See the
:mod:`fsl.data.atlases` module.
"""


import fsl.data.atlases             as atlases
import fsleyes_widgets.utils.status as status

import fsleyes.strings as strings
from . import             base


class LoadAtlasAction(base.Action):
    """The ``LoadAtlasAction`` prompts the user to select a FSL atlas
    specification file. This file is then passed to the
    :func:`.fsl.data.atlases.addAtlas` function, to add the atlas
    to the :class:`.AtlasRegistry`.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``LoadAtlasAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, overlayList, displayCtx, self.__loadAtlas)
        self.__frame = frame


    def __loadAtlas(self):
        """Calls the :func:`loadAtlas` function. """

        if len(atlases.listAtlases()) == 0:
            atlases.rescanAtlases()

        loadAtlas(self.__frame)


def loadAtlas(parent=None):
    """Prompts the user to select an atlas specification file, and then
    loads the atlas.
    """

    import wx
    app = wx.GetApp()

    if parent is None:
        parent = app.GetTopWindow()

    msg = strings.titles[LoadAtlasAction, 'fileDialog']
    dlg = wx.FileDialog(parent,
                        message=msg,
                        wildcard='XML atlas specification|*.xml',
                        style=wx.FD_OPEN)

    if dlg.ShowModal() != wx.ID_OK:
        return

    path     = dlg.GetPath()
    errtitle = strings.titles[  LoadAtlasAction, 'error']
    errmsg   = strings.messages[LoadAtlasAction, 'error'].format(path)

    with status.reportIfError(errtitle, errmsg):
        atlases.addAtlas(path)
