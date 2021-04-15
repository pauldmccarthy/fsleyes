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

import numpy as np

import fsl.data.image                       as fslimage
import fsl.data.mesh                        as fslmesh
import fsl.data.melodicimage                as fslmelimage
import fsleyes_props                        as props

import fsleyes.actions                      as actions
import fsleyes.views.plotpanel              as plotpanel
import fsleyes.profiles.plotprofile         as plotprofile
import fsleyes.plotting.powerspectrumseries as psseries


log = logging.getLogger(__name__)


class PowerSpectrumPanel(plotpanel.OverlayPlotPanel):
    """The ``PowerSpectrumPanel`` class is an :class:`.OverlayPlotPanel` which
    plots power spectra of overlay data.  ``PowerSpectrumPanel`` uses
    :class:`.PowerSpectrumSeries` to plot the power spectra of overlay data.


    A couple of control panels may be shown on a ``PowerSpectrumPanel`` via
    :meth:`.ViewPanel.togglePanel`.

    .. autosummary::
       :nosignatures:

       ~fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsleyes.controls.powerspectrumcontrolpanel.PowerSpectrumControlPanel


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


    @staticmethod
    def defaultLayout():
        """Returns a list of control panel types to be added for the default
        power spectrum panel layout.
        """
        return ['PowerSpectrumToolBar',
                'OverlayListPanel',
                'PlotListPanel']



    @staticmethod
    def controlOrder():
        """Returns a list of control panel names, specifying the order in
        which they should appear in the  FSLeyes ortho panel settings menu.
        """
        return ['OverlayListPanel',
                'PlotListPanel',
                'PowerSpectrumToolBar',
                'PowerSpectrumControlPanel']


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

        self.initProfile(plotprofile.PlotProfile)


    def destroy(self):
        """Must be called when this ``PowerSpectrumPanel`` is no longer
        needed. Removes some property listeners, and calls
        :meth:`.OverlayPlotPanel.destroy`.
        """

        self.removeListener('plotFrequencies', self.name)
        self.removeListener('plotMelodicICs',  self.name)
        plotpanel.OverlayPlotPanel.destroy(self)


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``PowerSpectrumPanel``.
        """
        actionz = [self.screenshot,
                   self.importDataSeries,
                   self.exportDataSeries]

        names = [a.actionName if a is not None else None for a in actionz]
        return list(zip(names, actionz))


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Draws some
        :class:`.PowerSpectrumSeries` using the
        :meth:`.PlotPanel.drawDataSeries` method.
        """

        if not self or self.destroyed:
            return

        canvas = self.canvas
        pss    = self.getDataSeriesToPlot()

        for ps in pss:
            with props.suppress(ps, 'label'):
                ps.label = ps.makeLabel()

        canvas.drawDataSeries(extraSeries=pss)
        canvas.drawArtists()


    def createDataSeries(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.createDataSeries`. Creates a
        :class:`.PowerSpectrumSeries` instance for the given overlay.
        """

        displayCtx  = self.displayCtx
        overlayList = self.overlayList

        psargs = [overlay, overlayList, displayCtx, self.canvas]

        if isinstance(overlay, fslmesh.Mesh):
            ps        = psseries.MeshPowerSpectrumSeries(*psargs)
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'vertexData']

        elif isinstance(overlay, fslmelimage.MelodicImage) and \
             self.plotMelodicICs:

            ps        = psseries.MelodicPowerSpectrumSeries(*psargs)
            targets   = [displayCtx.getOpts(overlay)]
            propNames = ['volume']

        elif isinstance(overlay, fslimage.Image) and overlay.ndim > 3:

            if overlay.iscomplex:
                ps = psseries.ComplexPowerSpectrumSeries(*psargs)
            else:
                ps = psseries.VoxelPowerSpectrumSeries(*psargs)

            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'volumeDim']

        else:
            return None, None, None

        ps.colour    = self.getOverlayPlotColour(overlay)
        ps.lineStyle = self.getOverlayPlotStyle(overlay)
        ps.lineWidth = 2
        ps.alpha     = 1.0

        return ps, targets, propNames


    def prepareDataSeries(self, ps):
        """Overrides :meth:`.PlotPanel.prepareDataSeries`.  Performs some
        pre-processing on the data of the given :class:`.PowerSpectrumSeries`
        instance.
        """

        xdata, ydata = ps.getData()

        # if plotFrequencies is disabled, replace
        # the x axis data with sample numbers
        if (xdata is not None) and \
           (ydata is not None) and \
           (len(xdata) > 0)    and \
           not self.plotFrequencies:
            xdata = np.arange(len(ydata))

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
