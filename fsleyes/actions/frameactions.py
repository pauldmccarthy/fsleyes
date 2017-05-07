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


import os.path as op

from fsl.utils.platform import platform as fslplatform

import                    fsleyes
import fsleyes.frame   as frame
import fsleyes.actions as actions


def addViewPanel(self, vpType, *args, **kwargs):
    """Function shared by the add*Panel functions below. """
    vp = self.addViewPanel(vpType)
    self.viewPanelDefaultLayout(vp)
    vp.SetFocus()


def addOrthoPanel(self, *args, **kwargs):
    """Adds a new :class:`.OrthoPanel`."""
    from fsleyes.views.orthopanel import OrthoPanel
    addViewPanel(self, OrthoPanel, *args, **kwargs)


def addLightBoxPanel(self, *args, **kwargs):
    """Adds a new :class:`.LightBoxPanel`."""
    from fsleyes.views.lightboxpanel import LightBoxPanel
    addViewPanel(self, LightBoxPanel, *args, **kwargs)


def addTimeSeriesPanel(self, *args, **kwargs):
    """Adds a new :class:`.TimeSeriesPanel`."""
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    addViewPanel(self, TimeSeriesPanel, *args, **kwargs)


def addHistogramPanel(self, *args, **kwargs):
    """Adds a new :class:`.HistogramPanel`."""
    from fsleyes.views.histogrampanel import HistogramPanel
    addViewPanel(self, HistogramPanel, *args, **kwargs)


def addPowerSpectrumPanel(self, *args, **kwargs):
    """Adds a new :class:`.PowerSpectrumPanel`."""
    from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
    addViewPanel(self, PowerSpectrumPanel, *args, **kwargs)


def addShellPanel(self, *args, **kwargs):
    """Adds a new :class:`.ShellPanel`."""
    from fsleyes.views.shellpanel import ShellPanel
    addViewPanel(self, ShellPanel, *args, **kwargs)



def removeFocusedViewPanel(self, *args, **kwargs):
    """Removes the :class:`.ViewPanel` which currently has focus. """

    vp = self.getFocusedViewPanel()

    if vp is not None:
        self.removeViewPanel(vp)


def _changeOverlay(self, offset):
    """Used by :func:`selectNextOverlay` and :func:`selectPreviousOverlay`.
    Changes the currently selected overlay by the given offset.
    """

    overlayList = self.getOverlayList()

    if len(overlayList) in (0, 1):
        return

    viewPanel = self.getFocusedViewPanel()

    if viewPanel is None: displayCtx = self     .getDisplayContext()
    else:                 displayCtx = viewPanel.getDisplayContext()

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

    overlayList = self.getOverlayList()

    if len(overlayList) == 0:
        return

    viewPanel = self.getFocusedViewPanel()

    if viewPanel is None: displayCtx = self     .getDisplayContext()
    else:                 displayCtx = viewPanel.getDisplayContext()

    overlay = displayCtx.getSelectedOverlay()
    display = displayCtx.getDisplay(overlay)

    display.enabled = not display.enabled


def openHelp(self, *args, **kwargs):
    """Opens FSLeyes help in a web browser. """

    url = op.join(
        fsleyes.assetDir, 'userdoc', 'html', 'index.html')

    import fsleyes_widgets.utils.webpage as webpage

    # Show locally stored help files
    if op.exists(url):
        webpage.openFile(url)
    else:
        url = 'http://users.fmrib.ox.ac.uk/~paulmc/fsleyes_userdoc/'
        webpage.openPage(url)


def closeFSLeyes(self, *args, **kwargs):
    """Closes FSLeyes. """
    self.Close()


frame.FSLeyesFrame.addOrthoPanel           = actions.action(addOrthoPanel)
frame.FSLeyesFrame.addLightBoxPanel        = actions.action(addLightBoxPanel)
frame.FSLeyesFrame.addTimeSeriesPanel      = actions.action(addTimeSeriesPanel)
frame.FSLeyesFrame.addHistogramPanel       = actions.action(addHistogramPanel)
frame.FSLeyesFrame.addPowerSpectrumPanel   = actions.action(addPowerSpectrumPanel)
frame.FSLeyesFrame.addShellPanel           = actions.action(addShellPanel)
frame.FSLeyesFrame.removeFocusedViewPanel  = actions.action(removeFocusedViewPanel)
frame.FSLeyesFrame.selectNextOverlay       = actions.action(selectNextOverlay)
frame.FSLeyesFrame.selectPreviousOverlay   = actions.action(selectPreviousOverlay)
frame.FSLeyesFrame.toggleOverlayVisibility = actions.action(toggleOverlayVisibility)
frame.FSLeyesFrame.openHelp                = actions.action(openHelp)
frame.FSLeyesFrame.closeFSLeyes            = actions.action(closeFSLeyes)
