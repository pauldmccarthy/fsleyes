#!/usr/bin/env python
#
# showcommandline.py - The ShowCommandLineAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ShowCommandLineAction` class, an action
used by the :class:`.CanvasPanel` class. A couple of stand-alone functions
are also defined here:

.. autosummary::
   :nosignatures:

   showCommandLineArgs
   genCommandLineArgs
"""


import wx

import fsleyes_widgets.dialog as fsldlg
import fsleyes.strings        as strings
import fsleyes.parseargs      as parseargs
from . import                    base


class ShowCommandLineAction(base.Action):
    """The :class:`ShowCommandLineAction` class is an :mod:`.action` which is
    used by :class:`.CanvasPanel` instances to generate a FSLeyes command line
    string which can be used to re-create the scene shown in the panel.
    """


    def __init__(self, overlayList, displayCtx, panel):
        """Create a ``ShowCommandLineAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg panel:       The :class:`.CanvasPanel`.
        """
        base.Action.__init__(self, self.__showCommandLineArgs)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__panel       = panel
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __showCommandLineArgs(self):
        """Called when this action is executed. Calls the
        :func:`showCommandLineArgs` function.
        """
        showCommandLineArgs(self.__overlayList,
                            self.__displayCtx,
                            self.__panel)


def showCommandLineArgs(overlayList, displayCtx, canvas):
    """Generates command line arguments which can be used to re-create the
    scene shown on the given :class:`CanvasPanel`, and displays them
    to the user with a :class:`.TextEditDialog`.

    :arg overlayList: A :class:`.OverlayList` .
    :arg displayCtx:  A :class:`.DisplayContext` instance.
    :arg canvas:      A :class:`CanvasPanel` instance.
    """
    args = genCommandLineArgs(overlayList, displayCtx, canvas)
    dlg  = fsldlg.TextEditDialog(
        canvas,
        title=strings.messages[  canvas, 'showCommandLineArgs', 'title'],
        message=strings.messages[canvas, 'showCommandLineArgs', 'message'],
        text=' '.join(args),
        icon=wx.ICON_INFORMATION,
        style=(fsldlg.TED_OK        |
               fsldlg.TED_READONLY  |
               fsldlg.TED_MULTILINE |
               fsldlg.TED_COPY      |
               fsldlg.TED_COPY_MESSAGE))

    dlg.CentreOnParent()
    dlg.ShowModal()


def genCommandLineArgs(overlayList, displayCtx, canvas=None):
    """Called by the :func:`showCommandLineArgs` function. Generates
    command line arguments which can be used to re-create the scene
    currently shown on the given :class:`CanvasPanel`.

    :arg overlayList: A :class:`.OverlayList` .
    :arg displayCtx:  A :class:`.DisplayContext` instance.
    :arg canvas:      A :class:`CanvasPanel` instance. If ``None``,
                      scene arguments are not generated.

    :returns:         A list of command line arguments.
    """

    argv = ['fsleyes']

    # Add scene options
    if canvas is not None:
        sceneOpts = canvas.sceneOpts
        argv += parseargs.generateSceneArgs(
            overlayList,
            displayCtx,
            sceneOpts,
            exclude=['performance'])

    # Add display options for each overlay
    for overlay in displayCtx.getOrderedOverlays():

        fname   = overlay.dataSource
        ovlArgv = parseargs.generateOverlayArgs(overlay,
                                                overlayList,
                                                displayCtx)
        argv   += [fname] + ovlArgv

    return argv
