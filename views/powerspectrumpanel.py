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
import fsl.fsleyes.plotting.powerspectrumseries       as psseries
import fsl.fsleyes.controls.powerspectrumcontrolpanel as pscontrol
import fsl.fsleyes.colourmaps                         as fslcm
import fsl.data.image                                 as fslimage
import fsl.data.melodicimage                          as fslmelimage


log = logging.getLogger(__name__)


class PowerSpectrumPanel(plotpanel.PlotPanel):
    """The ``PowerSpectrumPanel`` class is a :class:`.PlotPanel` which plots
    power spectra of overlay data. The ``PowerSpectrumPanel`` shares much of
    its design with the :class:`.TimeSeriesPanel`.


    The ``PowerSpectrumPanel`` uses :class:`.PowerSpectrumSeries` to plot
    power spectra of :class:`.Image` overlays,
    """

    
    plotMelodicICs  = props.Boolean(default=True)
    """If ``True``, the power spectra of :class:`.MelodicImage` overlays are
    plotted using :class:`.MelodicPowerSpectrumSeries` instances. Otherwise,
    :class:`.MelodicImage` overlays are treated as regular :class:`.Image`
    overlays, and :class:`.VoxelPowerSpectrumSeries` are used for plotting.
    """


    plotFrequencies = props.Boolean(default=True)
    """If ``True``, the x axis is scaled so that it represents frequency.
    """


    showMode = props.Choice(('current', 'all', 'none'))
    """Defines which power spectra to plot.

    =========== ========================================================
    ``current`` The power spectrum for the currently selected overlay is
                plotted.
    ``all``     The power spectra for all compatible overlays in the
                :class:`.OverlayList` are plotted.
    ``none``    Only the ``PowerSpectrumSeries`` that are in the
                :attr:`.PlotPanel.dataSeries` list will be plotted.
    =========== ========================================================
    """

    
    def __init__(self, parent, overlayList, displayCtx):
        """
        """

        actionz = {
            'togglePowerSpectrumControl' : lambda *a: self.togglePanel(
                pscontrol.PowerSpectrumControlPanel,
                self,
                location=wx.TOP)
        }
        
        plotpanel.PlotPanel.__init__(self,
                                     parent,
                                     overlayList,
                                     displayCtx,
                                     actionz=actionz)

        figure = self.getFigure()

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False) 

        # A dictionary of
        # 
        #   {overlay : PowerSpectrumSeries}
        #
        # instances, one for each (compatible)
        # overlay in the overlay list
        self.__spectra      = {}
        self.__refreshProps = {}

        self       .addListener('plotFrequencies', self._name, self.draw)
        self       .addListener('showMode',        self._name, self.draw)
        self       .addListener('plotMelodicICs',
                                self._name,
                                self.__plotMelodicICsChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__overlayListChanged)
        
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__overlayListChanged()


    def destroy(self):
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        plotpanel.PlotPanel.destroy(self)


    def getDataSeries(self, overlay):
        return self.__spectra.get(overlay)
        

    def draw(self, *a):

        if self.showMode == 'all':
            overlays = self._overlayList[:]
        elif self.showMode == 'current':
            overlays = [self._displayCtx.getSelectedOverlay()]
        else:
            overlays = []

        pss = [self.__spectra.get(o) for o in overlays]
        pss = [ps for ps in pss if ps is not None]

        self.drawDataSeries(extraSeries=pss,
                            preproc=self.__prepareSpectrumData)

        
    def __overlayListChanged(self, *a):

        # Destroy any spectrum series for overlays
        # that have been removed from the list
        for ds in list(self.dataSeries):
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
                ds.destroy()

        for overlay, ds in list(self.__spectra.items()):
            if overlay not in self._overlayList:
                self.__clearCacheForOverlay(overlay)

        self.__updateCachedSpectra()
        self.draw()

        
    def __selectedOverlayChanged(self, *a):
        self.draw()

        
    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`plotMelodicICs` property changes. Re-creates
        the internally cached :class:`.TimeSeries` instances for all
        :class:`.MelodicImage` overlays in the :class:`.OverlayList`.
        """

        for overlay in self._overlayList:
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.__clearCacheForOverlay(overlay)

        self.__updateCachedSpectra()
        self.draw()


    def __clearCacheForOverlay(self, overlay):
        """Destroys the internally cached :class:`.TimeSeries` for the given
        overlay.
        """
        
        ts                 = self.__spectra     .pop(overlay, None)
        targets, propNames = self.__refreshProps.pop(overlay, ([], []))

        if ts is not None:
            ts.destroy()

        for t, p in zip(targets, propNames):
            t.removeListener(p, self._name)


    def __updateCachedSpectra(self):
        # Create a new spectrum series for overlays
        # which have been added to the list
        for overlay in self._overlayList:
            
            ss = self.__spectra.get(overlay)
            
            if ss is None:

                ss, targets, propNames = self.__createSpectrumSeries(overlay)

                if ss is None:
                    continue

                self.__spectra[     overlay] = ss
                self.__refreshProps[overlay] = targets, propNames

            ss.addGlobalListener(self._name, self.draw, overwrite=True)

        for targets, propNames in self.__refreshProps.values():
            for t, p in zip(targets, propNames):
                t.addListener(p, self._name, self.draw, overwrite=True)
                

    def __createSpectrumSeries(self, overlay):

        if self.plotMelodicICs and \
           isinstance(overlay, fslmelimage.MelodicImage):
            
            ps        = psseries.MelodicPowerSpectrumSeries(overlay,
                                                            self._displayCtx)
            targets   = [self._displayCtx.getOpts(overlay)]
            propNames = ['volume']
            
        elif isinstance(overlay, fslimage.Image):
            
            ps        = psseries.VoxelPowerSpectrumSeries(overlay,
                                                          self._displayCtx)
            targets   = [self._displayCtx]
            propNames = ['location']
            
        else:
            return None, [], []

        ps.colour    = fslcm.randomDarkColour()
        ps.alpha     = 1.0
        ps.lineWidth = 1
        ps.lineStyle = '-'
            
        return ps, targets, propNames


    def __prepareSpectrumData(self, ps):

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
