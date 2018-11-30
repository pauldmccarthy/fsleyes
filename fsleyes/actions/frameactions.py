#!/usr/bin/env python
#
# frameactions.py - Top level actions
#
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains various top-level FSLeyes actions which are
monkey-patched into the :class:`.FSLeyesFrame` class.
"""


import            os
import os.path as op

import                      fsleyes
import fsleyes.actions   as actions
import fsleyes.strings   as strings
from   fsleyes.frame import FSLeyesFrame



def addViewPanel(self, vpType, **kwargs):
    """Function shared by the add*Panel functions below. """
    vp = self.addViewPanel(vpType, **kwargs)
    self.viewPanelDefaultLayout(vp)
    vp.SetFocus()
    return vp


def addOrthoPanel(self, *args, **kwargs):
    """Adds a new :class:`.OrthoPanel`."""
    from fsleyes.views.orthopanel import OrthoPanel
    addViewPanel(self, OrthoPanel)


def addLightBoxPanel(self, *args, **kwargs):
    """Adds a new :class:`.LightBoxPanel`."""
    from fsleyes.views.lightboxpanel import LightBoxPanel
    addViewPanel(self, LightBoxPanel)


def addScene3DPanel(self, *args, **kwargs):
    """Adds a new :class:`.Scene3DPanel`."""
    from fsleyes.views.scene3dpanel import Scene3DPanel
    addViewPanel(self, Scene3DPanel)


def addTimeSeriesPanel(self, *args, **kwargs):
    """Adds a new :class:`.TimeSeriesPanel`."""
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    addViewPanel(self, TimeSeriesPanel)


def addHistogramPanel(self, *args, **kwargs):
    """Adds a new :class:`.HistogramPanel`."""
    from fsleyes.views.histogrampanel import HistogramPanel
    addViewPanel(self, HistogramPanel)


def addPowerSpectrumPanel(self, *args, **kwargs):
    """Adds a new :class:`.PowerSpectrumPanel`."""
    from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
    addViewPanel(self, PowerSpectrumPanel)


def addShellPanel(self, *args, **kwargs):
    """Adds a new :class:`.ShellPanel`."""
    from fsleyes.views.shellpanel import ShellPanel
    addViewPanel(self, ShellPanel)


def removeFocusedViewPanel(self, *args, **kwargs):
    """Removes the :class:`.ViewPanel` which currently has focus. """

    vp = self.focusedViewPanel

    if vp is not None:
        self.removeViewPanel(vp)


def _changeOverlay(self, offset):
    """Used by :func:`selectNextOverlay` and :func:`selectPreviousOverlay`.
    Changes the currently selected overlay by the given offset.
    """

    overlayList = self.overlayList

    if len(overlayList) in (0, 1):
        return

    viewPanel = self.focusedViewPanel

    if viewPanel is None: displayCtx = self     .displayCtx
    else:                 displayCtx = viewPanel.displayCtx

    cur = displayCtx.overlayOrder.index(displayCtx.selectedOverlay)
    new = displayCtx.overlayOrder[(cur + offset) % len(overlayList)]

    displayCtx.selectedOverlay = new


def selectNextOverlay(self, *args, **kwargs):
    """Increments the :attr:`.DisplayContext.selectedOverlay`. """
    _changeOverlay(self, 1)


def selectPreviousOverlay(self, *args, **kwargs):
    """Decrements the :attr:`.DisplayContext.selectedOverlay`. """
    _changeOverlay(self, -1)


def toggleOverlayVisibility(self, *args, **kwargs):
    """Shows/hides the currently selected overlay. """

    overlayList = self.overlayList

    if len(overlayList) == 0:
        return

    viewPanel = self.focusedViewPanel

    if viewPanel is None: displayCtx = self     .displayCtx
    else:                 displayCtx = viewPanel.displayCtx

    overlay = displayCtx.getSelectedOverlay()
    display = displayCtx.getDisplay(overlay)

    display.enabled = not display.enabled


def openHelp(self, *args, **kwargs):
    """Opens FSLeyes help in a web browser. """

    url = op.join(fsleyes.assetDir, 'userdoc', 'index.html')

    import fsleyes_widgets.utils.webpage as webpage

    # Show locally stored help files
    if op.exists(url):
        webpage.openFile(url)
    else:
        url = 'https://users.fmrib.ox.ac.uk/~paulmc/fsleyes/userdoc/'
        webpage.openPage(url)


def setFSLDIR(self, *args, **kwargs):
    """Opens a directory dialog allowing the user to select a value for
    ``$FSLDIR``.
    """

    import wx
    from   fsl.utils.platform import platform
    import fsl.utils.settings as     settings

    fsldir = platform.fsldir

    if fsldir is None:
        fsldir = os.getcwd()

    msg = strings.titles[self, 'setFSLDIR']

    dlg = wx.DirDialog(self,
                       message=msg,
                       defaultPath=fsldir,
                       style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

    if dlg.ShowModal() != wx.ID_OK:
        return

    fsldir                 = dlg.GetPath()
    platform.fsldir        = fsldir
    settings.write('fsldir', fsldir)


def closeFSLeyes(self, *args, **kwargs):
    """Closes FSLeyes. """
    self.Close()


FSLeyesFrame.addOrthoPanel           = actions.action(addOrthoPanel)
FSLeyesFrame.addLightBoxPanel        = actions.action(addLightBoxPanel)
FSLeyesFrame.addScene3DPanel         = actions.action(addScene3DPanel)
FSLeyesFrame.addTimeSeriesPanel      = actions.action(addTimeSeriesPanel)
FSLeyesFrame.addHistogramPanel       = actions.action(addHistogramPanel)
FSLeyesFrame.addPowerSpectrumPanel   = actions.action(addPowerSpectrumPanel)
FSLeyesFrame.addShellPanel           = actions.action(addShellPanel)
FSLeyesFrame.removeFocusedViewPanel  = actions.action(removeFocusedViewPanel)
FSLeyesFrame.selectNextOverlay       = actions.action(selectNextOverlay)
FSLeyesFrame.selectPreviousOverlay   = actions.action(selectPreviousOverlay)
FSLeyesFrame.toggleOverlayVisibility = actions.action(toggleOverlayVisibility)
FSLeyesFrame.openHelp                = actions.action(openHelp)
FSLeyesFrame.setFSLDIR               = actions.action(setFSLDIR)
FSLeyesFrame.closeFSLeyes            = actions.action(closeFSLeyes)
