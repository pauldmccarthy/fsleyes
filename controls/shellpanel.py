#!/usr/bin/env python
#
# shellpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import wx.py.shell as wxshell

import fsl.fsleyes.panel as fslpanel


class ShellPanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, sceneOpts):
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        lcls = {
            'displayCtx'  : displayCtx,
            'overlayList' : overlayList,
            'sceneOpts'   : sceneOpts,
            'viewPanel'   : parent,
        }

        shell = wxshell.Shell(
            self,
            introText='   FSLEyes python shell\n\n'
                      'Available variables are:\n'
                      '  - overlayList\n' 
                      '  - displayCtx\n'
                      '  - sceneOpts\n\n',
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
        fslpanel.FSLEyesPanel.destroy(self)
