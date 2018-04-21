#!/usr/bin/env python
#
# timeseriesprofile.py - The TimeSeriesProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.TimeSeriesProfile` class, an interaction
profile for the :class:`.TimeSeriesPanel`.
"""


import fsl.utils.idle        as idle
import fsl.data.image        as fslimage
import fsl.data.melodicimage as fslmelimage
from . import                   plotprofile


class TimeSeriesProfile(plotprofile.PlotProfile):
    """The ``TimeSeriesProfile`` is a :class:`.PlotProfile` for use with the
    :class:`.TimeSeriesPanel`.

    In addition to the ``panzoom`` mode provided by the :class:`.PlotProfile`
    class, the ``TimeSeriesProfile`` class implements a ``volume`` mode, in
    which the user is able to click/drag on a plot to change the
    :attr:`.VolumeOpts.volume` for the currently selected overlay.
    """


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create a ``TimeSeriesProfile``.

        :arg viewPanel:    A :class:`.TimeSeriesPanel` instance.

        :arg overlayList:  The :class:`.OverlayList` instance.

        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """
        plotprofile.PlotProfile.__init__(self,
                                         viewPanel,
                                         overlayList,
                                         displayCtx,
                                         ['volume'])

        self.__volumeLine = None


    def __volumeModeCompatible(self):
        """Returns ``True`` if a volume line can currently be shown, ``False``
        otherwise.
        """

        tsPanel = self.viewPanel
        overlay = self.displayCtx.getSelectedOverlay()
        display = self.displayCtx.getDisplay(overlay)

        if not isinstance(overlay, fslimage.Image):
            return False

        if display.overlayType not in ('volume', 'label', 'mask'):
            return False

        if isinstance(overlay, fslmelimage.MelodicImage) and \
           tsPanel.plotMelodicICs:
            return False

        if len(overlay.shape) < 4 or overlay.shape[3] == 1:
            return False

        return True


    def __updateVolume(self, volumeLine, xvalue):
        """Called by the ``volume`` event handlers. Updates the given
        ``volumeLine`` artist (assumed to be a ``matplotlib.Line2D``
        instance) so that it is located at the given ``xvalue``. Also
        updates  the :attr:`.VolumeOpts.volume` property  of the
        currently selected overlay accordingly.
        """

        tsPanel = self.viewPanel
        canvas  = tsPanel.getCanvas()
        overlay = self.displayCtx.getSelectedOverlay()
        opts    = self.displayCtx.getOpts(overlay)

        if xvalue is None:
            return

        if tsPanel.usePixdim: volume = round(xvalue / overlay.pixdim[3])
        else:                 volume = round(xvalue)

        if volume <  0:                volume = 0
        if volume >= overlay.shape[3]: volume = overlay.shape[3] - 1

        if tsPanel.usePixdim: xvalue = volume * overlay.pixdim[3]
        else:                 xvalue = volume

        volumeLine.set_xdata(xvalue)
        canvas.draw()

        # Update the volume asynchronously,
        # and drop any previously enqueued
        # updates.
        def update():
            opts.volume = volume

        idle.idle(
            update,
            name='{}_{}_volume'.format(self.name, id(overlay)),
            dropIfQueued=True)


    def _volumeModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Adds a vertical line to the plot at the current volume. """

        if self.__volumeLine is not None:
            self.__volumeLine.remove()
            self.__volumeLine = None

        if not self.__volumeModeCompatible():
            return

        if canvasPos is None: xvalue = None
        else:                 xvalue = canvasPos[0]

        tsPanel = self.viewPanel
        axis    = tsPanel.getAxis()

        self.__volumeLine = axis.axvline(0, c='#000080', lw=3)

        self.__updateVolume(self.__volumeLine, xvalue)


    def _volumeModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Updates the position of the vertical volume line. """

        if self.__volumeLine is None:
            return

        if canvasPos is None: xvalue = None
        else:                 xvalue = canvasPos[0]

        self.__updateVolume(self.__volumeLine, xvalue)


    def _volumeModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Removes the vertical volume line. """

        if self.__volumeLine is None:
            return

        self.__volumeLine.remove()
        self.__volumeLine = None

        self.viewPanel.getCanvas().draw()
