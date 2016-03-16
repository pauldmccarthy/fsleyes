#!/usr/bin/env python
#
# shellpanel.py - The ShellPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ShellPanel` class, a *FSLeyes view*
which contains an interactive Python shell.
"""


import wx

import wx.py.shell as wxshell

from . import viewpanel

import fsl.fsleyes.actions.runscript as runscript


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
        
        :arg frame:       The :class:`.FSLEyesFrame` that owns this
                          ``ShellPanel``.
        """
        viewpanel.ViewPanel.__init__(self, parent, overlayList, displayCtx)

        _globals, _locals = runscript.fsleyesScriptEnvironment(frame,
                                                               overlayList,
                                                               displayCtx)


        shell = wxshell.Shell(
            self,
            introText='   FSLEyes python shell\n\n'
                      'Available FSLeyes variables are:\n'
                      '  - overlayList\n' 
                      '  - displayCtx\n'
                      '  - frame\n',
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
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)

        sizer.Add(shell, flag=wx.EXPAND, proportion=1)

        self.SetMinSize((300, 200))


    def destroy(self):
        """Must be called when this ``ShellPanel`` is no longer needed.
        Calls the :meth:`.FSLEyesPanel.destroy` method.
        """
        viewpanel.ViewPanel.destroy(self)
