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

import props

import                                                   plotpanel
import fsl.fsleyes.actions                            as actions
import fsl.fsleyes.plotting.powerspectrumseries       as psseries
import fsl.fsleyes.controls.powerspectrumcontrolpanel as pscontrol
import fsl.fsleyes.controls.plotlistpanel             as plotlistpanel
import fsl.data.image                                 as fslimage
import fsl.data.melodicimage                          as fslmelimage


log = logging.getLogger(__name__)


class PowerSpectrumPanel(plotpanel.OverlayPlotPanel):
    """The ``PowerSpectrumPanel`` class is an :class:`.OverlayPlotPanel` which
    plots power spectra of overlay data.  ``PowerSpectrumPanel`` uses
    :class:`.PowerSpectrumSeries` to plot power spectra of :class:`.Image`
    overlays,

    
    A couple of control panels may be shown on a ``PowerSpectrumPanel``:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsl.fsleyes.controls.powerspectrumcontrolpanel.PowerSpectrumControlPanel

    
    The following actions are provided, in addition to those already provided
    by the :class:`.PlotPanel`:

    .. autosummary::
       :nosignatures:

       togglePowerSpectrumList
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

    
    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``PowerSpectrumPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        
        plotpanel.OverlayPlotPanel.__init__(self,
                                            parent,
                                            overlayList,
                                            displayCtx)


        self.addListener('plotFrequencies', self._name, self.draw)
        self.addListener('plotMelodicICs',
                                self._name,
                                self.__plotMelodicICsChanged)


    def destroy(self):
        """Must be called when this ``PowerSpectrumPanel` is no longer
        needed. Removes some property listeners, and calls
        :meth:`.OverlayPlotPanel.destroy`.
        """
        
        self.removeListener('plotFrequencies', self._name)
        self.removeListener('plotMelodicICs',  self._name)
        plotpanel.OverlayPlotPanel.destroy(self)


    @actions.toggleControlAction(pscontrol.PowerSpectrumControlPanel)
    def togglePowerSpectrumControl(self):
        """Shows/hides a :class:`.PowerSpectrumControlPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(pscontrol.PowerSpectrumControlPanel,
                         self,
                         location=wx.TOP)

        
    @actions.toggleControlAction(plotlistpanel.PlotListPanel)
    def togglePowerSpectrumList(self):
        """Shows/hides a :class:`.PlotListPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """ 
        self.togglePanel(plotlistpanel.PlotListPanel,
                         self,
                         location=wx.TOP) 

        
    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``PowerSpectrumPanel``.
        """
        actions = [self.screenshot,
                   self.togglePowerSpectrumList,
                   self.togglePowerSpectrumControl]

        names = [a.__name__ for a in actions]

        return zip(names, actions)


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Draws some
        :class:`.PowerSpectrumSeries` using the
        :meth:`.PlotPanel.drawDataSeries` method.
        """

        if self.showMode == 'all':
            overlays = self._overlayList[:]
        elif self.showMode == 'current':
            overlays = [self._displayCtx.getSelectedOverlay()]
        else:
            overlays = []

        pss = [self.getDataSeries(o) for o in overlays]
        pss = [ps for ps in pss if ps is not None]

        for ps in pss:
            ps.label = ps.makeLabel() 

        self.drawDataSeries(extraSeries=pss,
                            preproc=self.__prepareSpectrumData)


    def createDataSeries(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.createDataSeries`. Creates a
        :class:`.PowerSpectrumSeries` instance for the given overlay.
        """

        if self.plotMelodicICs and \
           isinstance(overlay, fslmelimage.MelodicImage):
            
            ps        = psseries.MelodicPowerSpectrumSeries(overlay,
                                                            self._displayCtx)
            targets   = [self._displayCtx.getOpts(overlay)]
            propNames = ['volume']
            
        elif isinstance(overlay, fslimage.Image) and \
             overlay.is4DImage():
            
            ps        = psseries.VoxelPowerSpectrumSeries(overlay,
                                                          self._displayCtx)
            targets   = [self._displayCtx]
            propNames = ['location']
            
        else:
            return None, None, None

        ps.colour    = self.getOverlayPlotColour(overlay)
        ps.alpha     = 1.0
        ps.lineWidth = 1
        ps.lineStyle = '-'
            
        return ps, targets, propNames


    def __prepareSpectrumData(self, ps):
        """Performs some pre-processing on the data of the given
        :class:`.PowerSpectrumSeries` instance. This method is used as the
        ``preproc`` argument to the :meth:`.PlotPanel.drawDataSeries` method,
        in :meth:`draw`.
        """

        xdata, ydata = ps.getData()

        if self.plotFrequencies:

            nsamples   = len(ydata)
            sampleTime = 1

            if isinstance(ps.overlay, fslmelimage.MelodicImage):
                sampleTime = ps.overlay.tr
            elif isinstance(ps.overlay, fslimage.Image):
                sampleTime = ps.overlay.pixdim[3]

            freqStep = 1.0 / (2 * nsamples * sampleTime)
            xdata    = np.arange(0.0, nsamples * freqStep, freqStep)

        return xdata, ydata

        
    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`plotMelodicICs` property changes. Re-creates
        the internally cached :class:`.PowerSpectrmSeries` instances for all
        :class:`.MelodicImage` overlays in the :class:`.OverlayList`.
        """
        
        for overlay in self._overlayList:
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.clearDataSeries(overlay)

        self.updateDataSeries()
        self.draw()
