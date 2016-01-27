#!/usr/bin/env python
#
# shellpanel.py - The ShellPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ShellPanel` class, a *FSLeyes control*
which contains an interactive Python shell.
"""


import wx

import wx.py.shell as wxshell

import fsl.fsleyes.panel as fslpanel


class ShellPanel(fslpanel.FSLEyesPanel):
    """A ``ShellPanel`` is a :class:`.FSLEyesPanel` which contains an
    interactive Python shell.

    A ``ShellPanel`` allows the user to programmatically interact with the
    :class:`.OverlayList`, and with the :class:`.DisplayContext` and
    :class:`.SceneOpts` instances associated with the :class:`.CanvasPanel`
    that owns this ``ShellPanel``.
    """

    def __init__(self, parent, overlayList, displayCtx, canvasPanel):
        """Create a ``ShellPanel``.

        :arg parent:      The :mod:`wx` parent object, assumed to be the
                          :class:`.CanvasPanel` that owns this ``ShellPanel``.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The :class:`.DisplayContext` of the
                          :class:`.CanvasPanel` that owns this ``ShellPanel``.
        
        :arg canvasPanel: The :class:`.CanvasPanel` that owns this
                          ``ShellPanel``.
        """
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        lcls = {
            'displayCtx'  : displayCtx,
            'overlayList' : overlayList,
            'sceneOpts'   : canvasPanel.getSceneOptions(),
            'viewPanel'   : parent,
        }

        shell = wxshell.Shell(
            self,
            introText='   FSLEyes python shell\n\n'
                      'Available variables are:\n'
                      '  - overlayList\n' 
                      '  - displayCtx\n'
                      '  - sceneOpts\n\n'
                      '  - viewPanel\n\n', 
            locals=lcls,
            showInterpIntro=False)

        # TODO set up environment so that users can
        #
        #   - load/add overlays to list
        #
        #   - Load overlays from a URL
        #
        #   - make plots - already possible with pylab, but make
        #     sure it works properly (i.e. doesn't clobber the shell)
        #
        #   - run scripts (add a 'load/run' button)
        #
        #   - open/close view panels, and manipulate existing view panels
        #   
        shell.push('from pylab import *\n')

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
        fslpanel.FSLEyesPanel.destroy(self)
