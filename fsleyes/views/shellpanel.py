#!/usr/bin/env python
#
# shellpanel.py - The ShellPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ShellPanel` class, a *FSLeyes view*
which contains an interactive Python shell.
"""


import re
import sys
import textwrap

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

        descWidth   = 60
        varWidth    = max([len(v) for v in localVars])

        localDescs = [d[:descWidth + 30]   for d in localDescs]
        localDescs = [d.replace('\n', ' ') for d in localDescs]
        localDescs = [re.sub(' +', ' ', d) for d in localDescs]
        localDescs = [d[:descWidth]        for d in localDescs]

        shortFmtStr = '  - {{:{:d}s}} : {{}}\n'   .format(varWidth)
        longFmtStr  = '  - {{:{:d}s}} : {{}}...\n'.format(varWidth)

        for lvar, ldesc in zip(localVars, localDescs):

            if len(ldesc) >= descWidth: fmt = longFmtStr
            else:                       fmt = shortFmtStr

            introText = introText + fmt.format(lvar, ldesc)

        introText = introText + textwrap.dedent("""

        Type help(item) for additional details on a specific item.
        """)

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
        self.centrePanel = shell


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
#
# The Interpreter_* function is monkey-patched
# into the wx.py.interpreter.Interpreter class,
# because the original version is unable to
# execute multi-line statements.


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
