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
import fsleyes.displaycontext as displaycontext
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


def genCommandLineArgs(overlayList, displayCtx, canvas):
    """Called by the :func:`showCommandLineArgs` function. Generates
    command line arguments which can be used to re-create the scene
    currently shown on the given :class:`CanvasPanel`.

    :arg overlayList: A :class:`.OverlayList` .
    :arg displayCtx:  A :class:`.DisplayContext` instance.
    :arg canvas:      A :class:`CanvasPanel` instance.

    :returns:         A list of command line arguments.
    """

    argv = ['fsleyes']

    # Add scene options
    sceneOpts = canvas.getSceneOptions()
    argv += parseargs.generateSceneArgs(
        overlayList,
        displayCtx,
        sceneOpts,
        exclude=['performance'])

    # Add ortho specific options, if it's
    # an orthopanel we're dealing with
    if isinstance(sceneOpts, displaycontext.OrthoOpts):

        xcanvas = canvas.getXCanvas()
        ycanvas = canvas.getYCanvas()
        zcanvas = canvas.getZCanvas()

        # Get the canvas centres in the
        # display coordinate system
        xc = xcanvas.getDisplayCentre()
        yc = ycanvas.getDisplayCentre()
        zc = zcanvas.getDisplayCentre()

        # The getDisplayCentre method only
        # returns horizontal/vertical values,
        # so we have to make the positions 3D.
        loc = displayCtx.location.xyz
        xc  = [loc[0], xc[ 0], xc[ 1]]
        yc  = [yc[ 0], loc[1], yc[ 1]]
        zc  = [zc[ 0], zc[ 1], loc[2]]

        # Transform the centres into the world
        # coordinate system of the first overlay.
        if len(overlayList) > 0:
            opts   = displayCtx.getOpts(overlayList[0])
            refimg = opts.getReferenceImage()

            if refimg is not None:
                opts       = displayCtx.getOpts(refimg)
                xc, yc, zc = opts.transformCoords(
                    [xc, yc, zc], 'display', 'world')

            # And turn back into 2D (horizontal/
            # vertical) positions
            xc = xc[1], xc[2]
            yc = yc[0], yc[2]
            zc = zc[0], zc[1]

        argv += ['--{}'.format(parseargs.ARGUMENTS[sceneOpts, 'xcentre'][1])]
        argv += ['{:0.8f}'.format(c) for c in xc]
        argv += ['--{}'.format(parseargs.ARGUMENTS[sceneOpts, 'ycentre'][1])]
        argv += ['{:0.8f}'.format(c) for c in yc]
        argv += ['--{}'.format(parseargs.ARGUMENTS[sceneOpts, 'zcentre'][1])]
        argv += ['{:0.8f}'.format(c) for c in zc]

    # Add display options for each overlay
    for overlay in overlayList:

        fname   = overlay.dataSource
        ovlArgv = parseargs.generateOverlayArgs(overlay, displayCtx)
        argv   += [fname] + ovlArgv

    return argv
