#!/usr/bin/env python
#
# shellpanel.py - The ShellPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ShellPanel` class, a *FSLeyes view*
which contains an interactive Python shell.
"""


import os
import sys
import string
import textwrap

import                      wx
import wx.py.shell       as wxshell
import wx.py.interpreter as wxinterpreter

import fsleyes.version           as version
import fsleyes.actions.runscript as runscript
from . import                       viewpanel



class ShellPanel(viewpanel.ViewPanel):
    """A ``ShellPanel`` is a :class:`.ViewPanel` which contains an
    interactive Python shell.

    A ``ShellPanel`` allows the user to programmatically interact with the
    :class:`.OverlayList`, and with the :class:`.DisplayContext` and
    :class:`.SceneOpts` instances associated with the :class:`.CanvasPanel`
    that owns this ``ShellPanel``.
    """

    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``ShellPanel``.

        :arg parent:      The :mod:`wx` parent object, assumed to be the
                          :class:`.CanvasPanel` that owns this ``ShellPanel``.

        :arg overlayList: The :class:`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` of the
                          :class:`.CanvasPanel` that owns this ``ShellPanel``.

        :arg frame:       The :class:`.FSLeyesFrame` that owns this
                          ``ShellPanel``.
        """
        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        _globals, _locals = runscript.fsleyesScriptEnvironment(frame,
                                                               overlayList,
                                                               displayCtx)

        introText = textwrap.dedent("""
          FSLeyes {} python shell (Python {})

        Available items:
        """.format(version.__version__, sys.version.split()[0]))

        overrideDocs = {
            'np'  : 'numpy',
            'sp'  : 'scipy',
            'mpl' : 'matplotlib',
            'plt' : 'matplotlib.pyplot',
        }

        localVars  = list(_locals.keys())
        localDescs = [_locals[k].__doc__
                      if k not in overrideDocs
                      else overrideDocs[k]
                      for k in localVars]

        localDescs = [d.split('\n')[0].strip()[:60] for d in localDescs]

        varWidth  = max([len(v) for v in localVars])

        fmtStr = '  - {{:{:d}s}} : {{}}...\n'.format(varWidth)

        for lvar, ldesc in zip(localVars, localDescs):
            introText = introText + fmtStr.format(lvar, ldesc)

        shell = wxshell.Shell(
            self,
            introText=introText,
            locals=_locals,
            showInterpIntro=False)

        # TODO set up environment so that users can
        #
        #   - load/add overlays to list
        #
        #   - Load overlays from a URL
        #
        #   - make plots
        #
        #   - run scripts (add a 'load/run' button)
        #
        #   - open/close view panels, and manipulate existing view panels
        #

        font = shell.GetFont()
        shell.SetFont(font.Larger())
        self.setCentrePanel(shell)


    def destroy(self):
        """Must be called when this ``ShellPanel`` is no longer needed.
        Calls the :meth:`.FSLeyesPanel.destroy` method.
        """
        viewpanel.ViewPanel.destroy(self)


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Currently returns
        an empty list.
        """
        return []


# The wx.Shell code was written many years ago,
# and there are loads of things wrong with it.

# The Shell_* functions are monkey-patched into
# the wx.py.shell.Shell class, as the originals
# do not correctly decode pasted text under OSX.
# Without these patches, pasting text from the
# clipboard into the shell will result in random
# unicode characters appearing.

# The Interpreter_* function is monkey-patched
# into the wx.py.interpreter.Interpreter class,
# because the original version is unable to
# execute multi-line statements.


def Shell_Paste(self):
    if self.CanPaste() and wx.TheClipboard.Open():
        ps2 = str(sys.ps2)
        if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
            data = wx.TextDataObject()
            data.SetFormat(wx.DataFormat(wx.DF_TEXT))
            if wx.TheClipboard.GetData(data):
                self.ReplaceSelection('')
                command = data.GetText()
                command = command.encode('unicode_internal')
                command = [x for x in command if x in string.printable]
                command = command.rstrip()
                command = self.fixLineEndings(command)
                command = self.lstripPrompt(text=command)
                command = command.replace(os.linesep + ps2, '\n')
                command = command.replace(os.linesep, '\n')
                command = command.replace('\n', os.linesep + ps2)
                self.write(command)
        wx.TheClipboard.Close()


def Shell_PasteAndRun(self):
    text = ''
    if wx.TheClipboard.Open():
        if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
            data = wx.TextDataObject()
            if wx.TheClipboard.GetData(data):
                text = data.GetText()
                text = text.encode('unicode_internal')
                text = [x for x in text if x in string.printable]
        wx.TheClipboard.Close()
    if text:
        self.Execute(text)


def Interpreter_runsource(self, source):
    from code import InteractiveInterpreter

    # Horrible hack - if there are newlines
    # in the source, compile it as 'exec',
    # otherwise compile it as 'single'
    if source.find('\n') > -1: symbol = 'exec'
    else:                      symbol = 'single'

    stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin, sys.stdout, sys.stderr = \
               self.stdin, self.stdout, self.stderr

    more = InteractiveInterpreter.runsource(self, source, symbol=symbol)

    # this was a cute idea, but didn't work...
    # more = self.runcode(compile(source,'',
    #               ('exec' if self.useExecMode else 'single')))

    # If sys.std* is still what we set it to, then restore it.
    # But, if the executed source changed sys.std*, assume it was
    # meant to be changed and leave it. Power to the people.
    if sys.stdin == self.stdin:
        sys.stdin = stdin
    else:
        self.stdin = sys.stdin
    if sys.stdout == self.stdout:
        sys.stdout = stdout
    else:
        self.stdout = sys.stdout
    if sys.stderr == self.stderr:
        sys.stderr = stderr
    else:
        self.stderr = sys.stderr
    return more


wxinterpreter.Interpreter.runsource = Interpreter_runsource
wxshell.Shell.Paste                 = Shell_Paste
wxshell.Shell.PasteAndRun           = Shell_PasteAndRun
