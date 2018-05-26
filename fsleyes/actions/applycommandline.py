#!/usr/bin/env python
#
# applycommandline.py - The ApplyCommandLineAction
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ApplyCommandLineAction` class, an
:class:`.Action` which allows the user to apply FSLeyes command line
arguments to a :class:`.CanvasPanel`. The stand-alone
:func:`applyCommandLineArgs` function is where the work is actually
implemented.
"""


import sys
import argparse
import six

import wx

import fsleyes_widgets.dialog       as fsldlg
import fsleyes_widgets.utils.status as status

import fsleyes.strings              as strings
import fsleyes.parseargs            as parseargs
from . import                          base


class ApplyCommandLineAction(base.Action):
    """The :class:`ApplyCommandLineAction` class is an :class:`.Action` which
    allows the user to apply FSLeyes command line arguments to a
    :class:`.CanvasPanel`.
    """


    def __init__(self, overlayList, displayCtx, panel):
        """Create an ``ApplyCommandLineAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg panel:       The :class:`.CanvasPanel`.
        """
        base.Action.__init__(self, self.__applyCommandLineArgs)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__panel       = panel
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __applyCommandLineArgs(self):
        """Called when this action is executed. Prompts the user to enter
        some command line arguments, and then passes them to the
        :func:`applyCommandLineArgs` function.
        """

        # prompt user for some arguments
        dlg = fsldlg.TextEditDialog(
            self.__panel,
            strings.titles[  self, 'title'],
            strings.messages[self, 'apply'],
            style=fsldlg.TED_MULTILINE | fsldlg.TED_OK_CANCEL)

        dlg.CentreOnParent()

        if dlg.ShowModal() != wx.ID_OK:
            return

        # Pass GetText through str, because it
        # returns a unicode string, and python's
        # argparse does not seem to like unicode.
        argv     = str(dlg.GetText()).split()
        errTitle = strings.titles[  self, 'error']
        errMsg   = strings.messages[self, 'error']

        # apply said arguments
        with status.reportIfError(errTitle, errMsg):
            applyCommandLineArgs(self.__overlayList,
                                 self.__displayCtx,
                                 argv,
                                 self.__panel)


class ApplyCLIExit(Exception):
    """``Exception`` class raised by the :func:`applyCommandLineArgs`
    function.
    """

    def __init__(self, code, stdout, stderr):
        self.code   = code
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return '\n'.join((self.stderr, self.stdout))


def applyCommandLineArgs(overlayList,
                         displayCtx,
                         argv,
                         panel=None,
                         applyOverlayArgs=True,
                         **kwargs):
    """Applies the command line arguments stored in ``argv`` to the
    :class:`.CanvasPanel` ``panel``. If ``panel is None``, it is assumed
    that ``argv`` only contains overlay arguments.

    :arg overlayList:      The :class:`.OverlayList`.

    :arg displayCtx:       The :class:`.DisplayContext`. If a ``panel`` is
                           provided, this should be the ``DisplayContext``
                           associated with that panel.

    :arg argv:             List of command line arguments to apply.
    :arg panel:            Optional :class:`.CanvasPanel` to apply the
                           arguments to.

    :arg applyOverlayArgs: If ``False``, overlay arguments are not applied.

    All other keyword arguments are passed to the
    :func:`.parseargs.applyOverlayArgs`  function.
    """

    # We patch sys.stdout/stderr
    # while parseargs.parseArgs is
    # called so we can capture its
    # output.
    stdout = six.StringIO()
    stderr = six.StringIO()

    if argv[0] == 'fsleyes':
        argv = argv[1:]

    parser = argparse.ArgumentParser(add_help=False)

    try:
        real_stdout = sys.stdout
        real_stderr = sys.stderr
        sys.stdout  = stdout
        sys.stderr  = stderr
        namespace   = parseargs.parseArgs(parser, argv, 'fsleyes')

    except SystemExit as e:
        raise ApplyCLIExit(e.code, stdout.getvalue(), stderr.getvalue())

    finally:
        sys.stdout = real_stdout
        sys.stderr = real_stderr

    if applyOverlayArgs:
        parseargs.applyOverlayArgs(
            namespace, overlayList, displayCtx, **kwargs)

    if panel is not None:
        sceneOpts = panel.sceneOpts
        parseargs.applySceneArgs(namespace, overlayList, displayCtx, sceneOpts)
