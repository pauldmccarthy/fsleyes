#!/usr/bin/env python
#
# frameactions.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op


from fsl.utils.platform import platform as fslplatform

import                    fsleyes
import fsleyes.frame   as frame
import fsleyes.actions as actions
import fsleyes.views   as views


def addOrthoPanel(self, *args, **kwargs):
    """Adds a new :class:`.OrthoPanel`."""
    vp = self.addViewPanel(views.OrthoPanel)
    self.viewPanelDefaultLayout(vp)


def addLightBoxPanel(self, *args, **kwargs):
    """Adds a new :class:`.LightBoxPanel`."""
    vp = self.addViewPanel(views.LightBoxPanel)
    self.viewPanelDefaultLayout(vp) 


def addTimeSeriesPanel(self, *args, **kwargs):
    """Adds a new :class:`.TimeSeriesPanel`."""
    vp = self.addViewPanel(views.TimeSeriesPanel)
    self.viewPanelDefaultLayout(vp)


def addHistogramPanel(self, *args, **kwargs):
    """Adds a new :class:`.HistogramPanel`."""
    vp = self.addViewPanel(views.HistogramPanel)
    self.viewPanelDefaultLayout(vp)


def addPowerSpectrumPanel(self, *args, **kwargs):
    """Adds a new :class:`.PowerSpectrumPanel`."""
    vp = self.addViewPanel(views.PowerSpectrumPanel)
    self.viewPanelDefaultLayout(vp)


def addShellPanel(self, *args, **kwargs):
    """Adds a new :class:`.ShellPanel`."""
    vp = self.addViewPanel(views.ShellPanel)
    self.viewPanelDefaultLayout(vp)


def removeFocusedViewPanel(self, *args, **kwargs):
    """Removes the :class:`.ViewPanel` which currently has focus. """

    vp = self.getFocusedViewPanel()

    if vp is not None:
        self.removeViewPanel(vp)


def openHelp(self, *args, **kwargs):
    """Opens FSLeyes help in a web browser. """

    if fslplatform.frozen:
        url = op.join(
            fsleyes.assetDir, 'userdoc', 'index.html')
    else:
        url = op.join(
            fsleyes.assetDir, 'userdoc', 'html', 'index.html')

    import fsl.utils.webpage as webpage

    # Show locally stored help files
    if op.exists(url):
        webpage.openFile(url)
    else:
        url = 'http://users.fmrib.ox.ac.uk/~paulmc/fsleyes/'
        webpage.openPage(url)


def closeFSLeyes(self, *args, **kwargs):
    """Closes FSLeyes. """
    self.Close()


frame.FSLEyesFrame.addOrthoPanel          = actions.action(addOrthoPanel)
frame.FSLEyesFrame.addLightBoxPanel       = actions.action(addLightBoxPanel)
frame.FSLEyesFrame.addTimeSeriesPanel     = actions.action(addTimeSeriesPanel)
frame.FSLEyesFrame.addHistogramPanel      = actions.action(addHistogramPanel)
frame.FSLEyesFrame.addPowerSpectrumPanel  = actions.action(addPowerSpectrumPanel)
frame.FSLEyesFrame.addShellPanel          = actions.action(addShellPanel)
frame.FSLEyesFrame.removeFocusedViewPanel = actions.action(removeFocusedViewPanel)
frame.FSLEyesFrame.openHelp               = actions.action(openHelp)
frame.FSLEyesFrame.closeFSLeyes           = actions.action(closeFSLeyes)
