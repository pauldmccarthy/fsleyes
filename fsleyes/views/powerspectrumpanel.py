#!/usr/bin/env python
#
# powerspectrumpanel.py - The PowerSpectrumPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumPanel` class, a
:class:`.ViewPanel` which plots frequency/power spectra.
"""


import logging

import wx

import numpy as np

import fsl.data.image                             as fslimage
import fsl.data.mesh                              as fslmesh
import fsl.data.melodicimage                      as fslmelimage
import fsleyes_props                              as props

import fsleyes.actions                            as actions
import fsleyes.plotting.powerspectrumseries       as psseries
import fsleyes.controls.powerspectrumcontrolpanel as pscontrol
import fsleyes.controls.powerspectrumtoolbar      as powerspectrumtoolbar
from . import                                        plotpanel


log = logging.getLogger(__name__)


class PowerSpectrumPanel(plotpanel.OverlayPlotPanel):
    """The ``PowerSpectrumPanel`` class is an :class:`.OverlayPlotPanel` which
    plots power spectra of overlay data.  ``PowerSpectrumPanel`` uses
    :class:`.PowerSpectrumSeries` to plot the power spectra of overlay data.


    A couple of control panels may be shown on a ``PowerSpectrumPanel``:

    .. autosummary::
       :nosignatures:

       ~fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsleyes.controls.powerspectrumcontrolpanel.PowerSpectrumControlPanel


    The following actions are provided, in addition to those already provided
    by the :class:`.PlotPanel`:

    .. autosummary::
       :nosignatures:

       togglePowerSpectrumToolBar
       togglePowerSpectrumControl


    **Melodic images**


    The :class:`.PowerSpectrumSeries` class uses a fourier transform to
    calculate the power spectrum of a time course.  However,
    :class:`.MelodicImage` overlays already have an associated power spectrum,
    meaning that there is no need to calculate one for them..  So for these
    overlays, a :class:`.MelodicPowerSpectrumSeries` instance is used.
    """


    plotMelodicICs  = props.Boolean(default=True)
    """If ``True``, the power spectra of :class:`.MelodicImage` overlays are
    plotted using :class:`.MelodicPowerSpectrumSeries` instances. Otherwise,
    :class:`.MelodicImage` overlays are treated as regular :class:`.Image`
    overlays, and :class:`.VoxelPowerSpectrumSeries` are used for plotting.
    """


    plotFrequencies = props.Boolean(default=True)
    """If ``True``, the x axis is scaled so that it represents frequency. """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``PowerSpectrumPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        plotpanel.OverlayPlotPanel.__init__(self,
                                            parent,
                                            overlayList,
                                            displayCtx,
                                            frame)

        self.addListener('plotFrequencies', self.name, self.draw)
        self.addListener('plotMelodicICs',
                                self.name,
                                self.__plotMelodicICsChanged)

        self.initProfile()


    def destroy(self):
        """Must be called when this ``PowerSpectrumPanel`` is no longer
        needed. Removes some property listeners, and calls
        :meth:`.OverlayPlotPanel.destroy`.
        """

        self.removeListener('plotFrequencies', self.name)
        self.removeListener('plotMelodicICs',  self.name)
        plotpanel.OverlayPlotPanel.destroy(self)


    @actions.toggleControlAction(pscontrol.PowerSpectrumControlPanel)
    def togglePowerSpectrumControl(self, floatPane=False):
        """Shows/hides a :class:`.PowerSpectrumControlPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(pscontrol.PowerSpectrumControlPanel,
                         self,
                         location=wx.RIGHT,
                         floatPane=floatPane)


    @actions.toggleControlAction(powerspectrumtoolbar.PowerSpectrumToolBar)
    def togglePowerSpectrumToolBar(self):
        """Shows/hides a :class:`.PlotToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(powerspectrumtoolbar.PowerSpectrumToolBar,
                         psPanel=self)


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``PowerSpectrumPanel``.
        """
        actions = [self.screenshot,
                   self.importDataSeries,
                   self.exportDataSeries,
                   None,
                   self.toggleOverlayList,
                   self.togglePlotList,
                   self.togglePowerSpectrumToolBar,
                   self.togglePowerSpectrumControl]

        names = [a.__name__ if a is not None else None for a in actions]

        return list(zip(names, actions))


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Draws some
        :class:`.PowerSpectrumSeries` using the
        :meth:`.PlotPanel.drawDataSeries` method.
        """

        if not self or self.destroyed():
            return

        pss = self.getDataSeriesToPlot()

        for ps in pss:
            with props.suppress(ps, 'label'):
                ps.label = ps.makeLabel()

        self.drawDataSeries(extraSeries=pss)
        self.drawArtists()


    def createDataSeries(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.createDataSeries`. Creates a
        :class:`.PowerSpectrumSeries` instance for the given overlay.
        """

        displayCtx  = self.displayCtx
        overlayList = self.overlayList

        psargs = [overlay, overlayList, displayCtx, self]

        if self.plotMelodicICs and \
           isinstance(overlay, fslmelimage.MelodicImage):

            ps        = psseries.MelodicPowerSpectrumSeries(*psargs)
            targets   = [displayCtx.getOpts(overlay)]
            propNames = ['volume']

        elif isinstance(overlay, fslimage.Image) and overlay.ndim > 3:

            ps        = psseries.VoxelPowerSpectrumSeries(*psargs)
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'volumeDim']

        elif isinstance(overlay, fslmesh.Mesh):
            ps        = psseries.MeshPowerSpectrumSeries(*psargs)
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'vertexData']

        else:
            return None, None, None

        ps.colour    = self.getOverlayPlotColour(overlay)
        ps.alpha     = 1.0
        ps.lineWidth = 1
        ps.lineStyle = '-'

        return ps, targets, propNames


    def prepareDataSeries(self, ps):
        """Overrides :meth:`.PlotPanel.prepareDataSeries`.  Performs some
        pre-processing on the data of the given :class:`.PowerSpectrumSeries`
        instance.
        """

        xdata, ydata = ps.getData()

        if len(xdata) > 0 and self.plotFrequencies:

            nsamples   = len(ydata)
            sampleTime = 1

            if isinstance(ps.overlay, fslmelimage.MelodicImage):
                sampleTime = ps.overlay.tr
            elif isinstance(ps.overlay, fslimage.Image):
                sampleTime = ps.overlay.pixdim[3]

            freqStep = 1.0 / (2 * nsamples * sampleTime)
            xdata    = np.linspace(0.0, (nsamples - 1) * freqStep, nsamples)

        return xdata, ydata


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`plotMelodicICs` property changes. Re-creates
        the internally cached :class:`.PowerSpectrmSeries` instances for all
        :class:`.MelodicImage` overlays in the :class:`.OverlayList`.
        """

        for overlay in self.overlayList:
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.clearDataSeries(overlay)

        self.updateDataSeries()
        self.draw()
