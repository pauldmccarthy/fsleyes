#!/usr/bin/env python
#
# screenshot.py - The ScreenshotAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ScreenshotAction` class, an
:class:`.Action` which can take screenshots of :class:`.CanvasPanel` and
:class:`.PlotPanel` views.


A few stand-alone functions are defined in this module:

.. autosummary::
   :nosignatures:

   screenshot
   plotPanelScreenshot
   canvasPanelScreenshot
"""


import            os
import os.path as op
import            logging

import                      wx
import numpy             as np
import matplotlib.pyplot as plt
import matplotlib.image  as mplimg

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.idle                     as idle
import fsleyes_widgets.utils.status       as status
import fsl.utils.settings                 as fslsettings
import fsleyes.views.canvaspanel          as canvaspanel
import fsleyes.views.plotpanel            as plotpanel

import fsleyes.strings as strings
from . import             base


log = logging.getLogger(__name__)


class ScreenshotAction(base.Action):
    """The ``ScreenshotAction`` is able to save a screenshot of the contents
    of :class:`.CanvasPanel` and :class:`.PlotPanel` views.
    """

    def __init__(self, overlayList, displayCtx, panel):
        """Create a ``ScreenshotAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg panel:       The :class:`.CanvasPanel` or :class:`.PlotPanel` to
                          take a screenshot of.
        """

        base.Action.__init__(self, self.__doScreenshot)
        self.__panel = panel


    def __doScreenshot(self):
        """Capture a screenshot. Prompts the user to select a file to save
        the screenshot to, and then calls the :func:`screenshot` function.
        """

        lastDirSetting = 'fsleyes.actions.screenshot.lastDir'

        # Ask the user where they want
        # the screenshot to be saved
        fromDir = fslsettings.read(lastDirSetting, os.getcwd())

        # We can get a list of supported output
        # types via a matplotlib figure object
        fig  = plt.figure()
        fmts = fig.canvas.get_supported_filetypes()

        # Default to png if
        # it is available
        if 'png' in fmts:
            fmts = [('png', fmts['png'])] + \
                   [(k, v) for k, v in fmts.items() if k is not 'png']
        else:
            fmts = list(fmts.items())

        wildcard = ['[*.{}] {}|*.{}'.format(fmt, desc, fmt)
                    for fmt, desc in fmts]
        wildcard = '|'.join(wildcard)
        filename = 'screenshot'

        dlg = wx.FileDialog(self.__panel,
                            message=strings.messages[self, 'screenshot'],
                            wildcard=wildcard,
                            defaultDir=fromDir,
                            defaultFile=filename,
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filename = dlg.GetPath()

        # Make the dialog go away before
        # the screenshot gets taken
        dlg.Close()
        dlg.Destroy()
        wx.GetApp().Yield()

        # Show an error if the screenshot
        # function raises an error
        doScreenshot = status.reportErrorDecorator(
            strings.titles[  self, 'error'],
            strings.messages[self, 'error'])(screenshot)

        # We do the screenshot asynchronously,
        # to make sure it is performed on
        # the main thread, during idle time
        idle.idle(doScreenshot, self.__panel, filename)

        status.update(strings.messages[self, 'pleaseWait'].format(filename))

        fslsettings.write(lastDirSetting, op.dirname(filename))


def screenshot(panel, filename):
    """Capture a screenshot of the contents of the given :class:`.CanvasPanel`
    or :class:`.PlotPanel`, saving it to the given ``filename``.
    """

    if isinstance(panel, canvaspanel.CanvasPanel):
        canvasPanelScreenshot(panel, filename)
    elif isinstance(panel, plotpanel.PlotPanel):
        plotPanelScreenshot(panel, filename)


def plotPanelScreenshot(panel, filename):
    """Capture a screenshot of the contents of the given :class:`.PlotPanel`
    or :class:`.PlotPanel`, saving it to the given ``filename``.
    """
    panel.getFigure().savefig(filename)


def canvasPanelScreenshot(panel, filename):
    """Capture a screenshot of the contents of the given :class:`.CanvasPanel`
    or :class:`.PlotPanel`, saving it to the given ``filename``.
    """

    # The canvas panel container is the
    # direct parent of the colour bar
    # canvas, and an ancestor of the
    # other GL canvases. So that's the
    # one that we want to take a screenshot
    # of.
    cpanel = panel
    opts   = panel.sceneOpts
    panel  = panel.containerPanel

    # Make a H*W*4 bitmap array (h*w because
    # that's how matplotlib want it). We
    # initialise the bitmap to the current
    # background colour, due to some sizing
    # issues that are discussed in the
    # osxPatch function below.
    bgColour      = np.array(opts.bgColour) * 255
    width, height = panel.GetClientSize().Get()
    data          = np.zeros((height, width, 4), dtype=np.uint8)
    data[:, :, :] = bgColour

    log.debug('Creating bitmap {} * {} for {} screenshot'.format(
        width, height, type(cpanel).__name__))

    # The typical way to get a screen grab of a
    # wx Window is to use a wx.WindowDC, and a
    # wx.MemoryDC, and to 'blit' a region from
    # the window DC into the memory DC. Then we
    # extract the bitmap data and copy it into
    # our array.
    windowDC = wx.WindowDC(panel)
    memoryDC = wx.MemoryDC()

    if fslplatform.wxFlavour == fslplatform.WX_PHOENIX:
        bmp = wx.Bitmap(width, height)
    else:
        bmp = wx.EmptyBitmap(width, height)

    # Copy the contents of the canvas
    # container to the bitmap
    memoryDC.SelectObject(bmp)
    memoryDC.Blit(
        0,
        0,
        width,
        height,
        windowDC,
        0,
        0)
    memoryDC.SelectObject(wx.NullBitmap)

    rgb = bmp.ConvertToImage().GetData()
    rgb = np.frombuffer(rgb, dtype=np.uint8)

    data[:, :, :3] = rgb.reshape(height, width, 3)

    # OSX and SSh/X11 both have complications
    inSSH = fslplatform.inSSHSession and not fslplatform.inVNCSession
    if inSSH or fslplatform.os == 'Darwin':
        data = _patchInCanvases(cpanel, panel, data, bgColour)

    data[:, :,  3] = 255

    try:              fmt = op.splitext(filename)[1][1:]
    except Exception: fmt = None

    mplimg.imsave(filename, data, format=fmt)


def _patchInCanvases(canvasPanel, containerPanel, data, bgColour):
    """Used by the :func:`canvasPanelScreenshot` function.

    For some unknown reason, under OSX and when running over X11/SSH, the
    contents of ``wx.glcanvas.GLCanvas`` instances are not captured by the
    ``WindowDC``/``MemoryDC`` blitting process performed by the
    ``canvasPanelScreenshot`` function - they come out all black.

    So this function manually patches in bitmaps (read from the GL front
    buffer) of each ``GLCanvas`` that is displayed in the canvas panel.
    """

    cpanel = canvasPanel
    panel  = containerPanel

    # Get all the wx GLCanvas instances
    # which are displayed in the panel,
    # including the colour bar canvas
    glCanvases = cpanel.getGLCanvases()
    glCanvases.append(cpanel.colourBarCanvas)

    # Note: These values are not scaled by the
    # display DPI (e.g. if using a retina display).
    # Hackiness below handles this situation.
    totalWidth, totalHeight = panel.GetClientSize().Get()
    absPosx,    absPosy     = panel.GetScreenPosition()

    # Patch in bitmaps for every GL canvas
    for glCanvas in glCanvases:

        # If the colour bar is not displayed,
        # the colour bar canvas will be None
        if glCanvas is None:
            continue

        # Hidden wx objects will
        # still return a size
        if not glCanvas.IsShown():
            continue

        scale         = glCanvas.GetScale()
        width, height = glCanvas.GetScaledSize()
        posx, posy    = glCanvas.GetScreenPosition()

        # make sure canvas position is scaled
        # by the display scaling factor.
        posx -= absPosx
        posy -= absPosy
        posx  = int(posx * scale)
        posy  = int(posy * scale)

        log.debug('Canvas {} position: ({}, {}); size: ({}, {})'.format(
            type(glCanvas).__name__, posx, posy, width, height))

        xstart = posx
        ystart = posy
        xend   = xstart + width
        yend   = ystart + height

        bmp = glCanvas.getBitmap()

        # Under OSX, there seems to be a size/position
        # miscalculation  somewhere, such that if the last
        # canvas is on the hard edge of the parent, the
        # canvas size spills over the parent size by a
        # couple of pixels. If this occurs, I re-size the
        # final bitmap accordingly.
        #
        # n.b. This is why I initialise the bitmap array
        #      to the canvas panel background colour.
        #
        # n.b. This code also (as a byproduct) handles
        #      high-DPI scaling, where the panel size
        #      is in unscaled pixels, but the canvas
        #      sizes/positions are scaled.
        if xend > totalWidth:

            oldWidth    = totalWidth
            totalWidth  = xend
            newData     = np.zeros((totalHeight, totalWidth, 4),
                                   dtype=np.uint8)

            newData[:, :, :]         = bgColour
            newData[:, :oldWidth, :] = data
            data                     = newData

            log.debug('Adjusted bitmap width: {} -> {}'.format(
                oldWidth, totalWidth))

        if yend > totalHeight:

            oldHeight   = totalHeight
            totalHeight = yend
            newData     = np.zeros((totalHeight, totalWidth, 4),
                                   dtype=np.uint8)

            newData[:, :, :]          = bgColour
            newData[:oldHeight, :, :] = data
            data                      = newData

            log.debug('Adjusted bitmap height: {} -> {}'.format(
                oldHeight, totalHeight))

        log.debug('Patching {} in at [{} - {}], [{} - {}]'.format(
            type(glCanvas).__name__, xstart, xend, ystart, yend))

        data[ystart:yend, xstart:xend] = bmp

    return data
