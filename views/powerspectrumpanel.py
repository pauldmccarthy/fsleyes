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
    power spectra of overlay data.
    """

    
    plotMelodicICs  = props.Boolean(default=True)
    """
    """


    plotFrequencies = props.Boolean(default=True)
    """
    """


    showMode = props.Choice(('current', 'all', 'none'))
    """
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
                self.__spectra.pop(overlay)
                ds.destroy()

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

        self.draw()

        
    def __selectedOverlayChanged(self, *a):
        self.draw()
        

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
