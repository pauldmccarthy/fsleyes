#!/usr/bin/env python
#
# timeseriespanel.py - A panel which plots time series/volume data from a
# collection of overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`wx.Panel` which plots time series/volume data from a collection
of overlay objects stored in an :class:`.OverlayList`.

:mod:`matplotlib` is used for plotting.

"""

import copy
import logging

import wx

import numpy as np

import                               props

import                               plotpanel
import fsl.data.featimage         as fslfeatimage
import fsl.data.image             as fslimage
import fsl.data.strings           as strings
import fsl.fsleyes.displaycontext as fsldisplay
import fsl.fsleyes.colourmaps     as fslcmaps
import fsl.fsleyes.controls       as fslcontrols


log = logging.getLogger(__name__)


class TimeSeries(plotpanel.DataSeries):

    
    def __init__(self, tsPanel, overlay, coords):
        plotpanel.DataSeries.__init__(self, overlay)

        self.tsPanel = tsPanel
        self.coords  = map(int, coords)
        self.data    = overlay.data[coords[0], coords[1], coords[2], :]


    def __copy__(self):

        return type(self)(self.tsPanel, self.overlay, self.coords)

        
    def update(self, coords):
        """This method is only intended for use on the 'current' time series,
        not for time series instances which have been added to the
        TimeSeries.dataSeries list
        """
        
        coords = map(int, coords)
        if coords == self.coords:
            return False
        
        self.coords = coords
        self.data   = self.overlay.data[coords[0], coords[1], coords[2], :]
        return True

        
    def getData(self, xdata=None, ydata=None):
        """
        
        :arg xdata:
        :arg ydata: Used by subclasses in case they have already done some
                    processing on the data.
        """

        if xdata is None: xdata = np.arange(len(self.data), dtype=np.float32)
        if ydata is None: ydata = np.array(     self.data,  dtype=np.float32)

        if self.tsPanel.usePixdim:
            xdata *= self.overlay.pixdim[3]
        
        if self.tsPanel.plotMode == 'demean':
            ydata = ydata - ydata.mean()

        elif self.tsPanel.plotMode == 'normalise':
            ymin  = ydata.min()
            ymax  = ydata.max()
            ydata = 2 * (ydata - ymin) / (ymax - ymin) - 1
            
        elif self.tsPanel.plotMode == 'percentChange':
            mean  = ydata.mean()
            ydata =  100 * (ydata / mean) - 100
            
        return xdata, ydata
    

 
class FEATTimeSeries(TimeSeries):
    """A :Class:`TimeSeries` class for use with :class:`FEATImage` instances,
    containing some extra FEAT specific options.
    """


    plotData         = props.Boolean(default=True)
    plotFullModelFit = props.Boolean(default=True)
    plotResiduals    = props.Boolean(default=False)
    plotEVs          = props.List(props.Boolean(default=False))
    plotPEFits       = props.List(props.Boolean(default=False))
    plotCOPEFits     = props.List(props.Boolean(default=False))
    plotReduced      = props.Choice()
    

    def __init__(self, *args, **kwargs):
        TimeSeries.__init__(self, *args, **kwargs)
        self.name = '{}_{}'.format(type(self).__name__, id(self))

        numEVs    = self.overlay.numEVs()
        numCOPEs  = self.overlay.numContrasts()
        copeNames = self.overlay.contrastNames()
        
        reduceOpts = ['none'] + \
                     ['PE{}'.format(i + 1) for i in range(numEVs)]

        for i in range(numCOPEs):
            name = 'COPE{} ({})'.format(i + 1, copeNames[i])
            reduceOpts.append(name)

        self.getProp('plotReduced').setChoices(reduceOpts, instance=self)

        for i in range(numEVs):
            self.plotPEFits.append(False)
            self.plotEVs   .append(False)

        for i in range(numCOPEs):
            self.plotCOPEFits.append(False) 

        self.__fullModelTs =  None
        self.__reducedTs   =  None
        self.__resTs       =  None
        self.__evTs        = [None] * numEVs
        self.__peTs        = [None] * numEVs
        self.__copeTs      = [None] * numCOPEs
        
        self.addListener('plotFullModelFit',
                         self.name,
                         self.__plotFullModelFitChanged)
        self.addListener('plotResiduals',
                         self.name,
                         self.__plotResidualsChanged)
        self.addListener('plotReduced',
                         self.name,
                         self.__plotReducedChanged)

        self.addListener('plotEVs',      self.name, self.__plotEVChanged)
        self.addListener('plotPEFits',   self.name, self.__plotPEFitChanged)
        self.addListener('plotCOPEFits', self.name, self.__plotCOPEFitChanged)

        # plotFullModelFit defaults to True, so
        # force the model fit ts creation here
        self.__plotFullModelFitChanged()


    def __copy__(self):
        
        copy = type(self)(self.tsPanel, self.overlay, self.coords)

        copy.colour           = self.colour
        copy.alpha            = self.alpha 
        copy.label            = self.label 
        copy.lineWidth        = self.lineWidth
        copy.lineStyle        = self.lineStyle

        # When these properties are changed 
        # on the copy instance, it will create 
        # its own FEATModelFitTimeSeries 
        # instances accordingly
        copy.plotFullModelFit = self.plotFullModelFit
        copy.plotEVs[     :]  = self.plotEVs[     :]
        copy.plotPEFits[  :]  = self.plotPEFits[  :]
        copy.plotCOPEFits[:]  = self.plotCOPEFits[:]
        copy.plotReduced      = self.plotReduced
        copy.plotResiduals    = self.plotResiduals

        return copy
 

    def getModelTimeSeries(self):
        
        modelts = []

        if self.plotData:              modelts.append(self)
        if self.plotFullModelFit:      modelts.append(self.__fullModelTs)
        if self.plotResiduals:         modelts.append(self.__resTs)
        if self.plotReduced != 'none': modelts.append(self.__reducedTs)
        
        for i in range(self.overlay.numEVs()):
            if self.plotPEFits[i]:
                modelts.append(self.__peTs[i])

        for i in range(self.overlay.numEVs()):
            if self.plotEVs[i]:
                modelts.append(self.__evTs[i]) 

        for i in range(self.overlay.numContrasts()):
            if self.plotCOPEFits[i]:
                modelts.append(self.__copeTs[i])

        return modelts


    def __getContrast(self, fitType, idx):

        if fitType == 'full':
            return [1] * self.overlay.numEVs()
        elif fitType == 'pe':
            con      = [0] * self.overlay.numEVs()
            con[idx] = 1
            return con
        elif fitType == 'cope':
            return self.overlay.contrasts()[idx]

        
    def __createModelTs(self, tsType, *args, **kwargs):

        ts = tsType(self.tsPanel, self.overlay, self.coords, *args, **kwargs)

        ts.alpha     = self.alpha
        ts.label     = self.label
        ts.lineWidth = self.lineWidth
        ts.lineStyle = self.lineStyle

        if   isinstance(ts, FEATReducedTimeSeries):  ts.colour = (0, 0.6, 0.6)
        elif isinstance(ts, FEATResidualTimeSeries): ts.colour = (0.8, 0.4, 0)
        elif isinstance(ts, FEATEVTimeSeries):       ts.colour = (0, 0.7, 0.35)
        elif isinstance(ts, FEATModelFitTimeSeries):
            if   ts.fitType == 'full': ts.colour = (0,   0, 1)
            elif ts.fitType == 'cope': ts.colour = (0,   1, 0)
            elif ts.fitType == 'pe':   ts.colour = (0.7, 0, 0)

        return ts


    def __plotReducedChanged(self, *a):
            
        reduced = self.plotReduced

        if reduced == 'none' and self.__reducedTs is not None:
            self.__reducedTs = None
            return

        reduced = reduced.split()[0]

        # fitType is either 'cope' or 'pe'
        fitType = reduced[:-1].lower()
        idx     = int(reduced[-1]) - 1

        self.__reducedTs = self.__createModelTs(
            FEATReducedTimeSeries,
            self.__getContrast(fitType, idx),
            fitType,
            idx) 


    def __plotResidualsChanged(self, *a):
        
        if not self.plotResiduals:
            self.__resTs = None
            return

        self.__resTs = self.__createModelTs(FEATResidualTimeSeries)


    def __plotEVChanged(self, *a):

        for evnum, plotEV in enumerate(self.plotEVs):

            if not self.plotEVs[evnum]:
                self.__evTs[evnum] = None
                
            elif self.__evTs[evnum] is None:
                self.__evTs[evnum] = self.__createModelTs(
                    FEATEVTimeSeries, evnum)
            
    
    def __plotCOPEFitChanged(self, *a):

        for copenum, plotCOPE in enumerate(self.plotCOPEFits):

            if not self.plotCOPEFits[copenum]:
                self.__copeTs[copenum] = None
            
            elif self.__copeTs[copenum] is None:
                self.__copeTs[copenum] = self.__createModelTs(
                    FEATModelFitTimeSeries,
                    self.__getContrast('cope', copenum),
                    'cope',
                    copenum)


    def __plotPEFitChanged(self, evnum):

        for evnum, plotPE in enumerate(self.plotPEFits):

            if not self.plotPEFits[evnum]:
                self.__peTs[evnum] = None

            elif self.__peTs[evnum] is None:
                self.__peTs[evnum] = self.__createModelTs(
                    FEATModelFitTimeSeries,
                    self.__getContrast('pe', evnum),
                    'pe',
                    evnum)


    def __plotFullModelFitChanged(self, *a):
        
        if not self.plotFullModelFit:
            self.__fullModelTs = None
            return

        self.__fullModelTs = self.__createModelTs(
            FEATModelFitTimeSeries, self.__getContrast('full', -1), 'full', -1)

        
    def update(self, coords):
        
        if not TimeSeries.update(self, coords):
            return False
            
        for modelTs in self.getModelTimeSeries():
            if modelTs is self:
                continue
            modelTs.update(coords)

        return True


class FEATReducedTimeSeries(TimeSeries):
    def __init__(self, tsPanel, overlay, coords, contrast, fitType, idx):
        TimeSeries.__init__(self, tsPanel, overlay, coords)

        self.contrast = contrast
        self.fitType  = fitType
        self.idx      = idx

    def getData(self):
        
        data = self.overlay.reducedData(self.coords, self.contrast, False)
        return TimeSeries.getData(self, ydata=data)

    
class FEATEVTimeSeries(TimeSeries):
    def __init__(self, tsPanel, overlay, coords, idx):
        TimeSeries.__init__(self, tsPanel, overlay, coords)
        self.idx = idx
        
    def getData(self):
        data = self.overlay.getDesign()[:, self.idx]
        return TimeSeries.getData(self, ydata=data)
    

class FEATResidualTimeSeries(TimeSeries):
    def getData(self):
        x, y, z = self.coords
        data    = self.overlay.getResiduals().data[x, y, z, :]
        
        return TimeSeries.getData(self, ydata=np.array(data))
            

class FEATModelFitTimeSeries(TimeSeries):

    def __init__(self, tsPanel, overlay, coords, contrast, fitType, idx):
        
        if fitType not in ('full', 'cope', 'pe'):
            raise ValueError('Unknown model fit type {}'.format(fitType))
        
        TimeSeries.__init__(self, tsPanel, overlay, coords)
        self.fitType  = fitType
        self.idx      = idx
        self.contrast = contrast
        self.updateModelFit()

        
    def update(self, coords):
        if not TimeSeries.update(self, coords):
            return
        self.updateModelFit()
        

    def updateModelFit(self):

        fitType   = self.fitType
        contrast  = self.contrast
        xyz       = self.coords
        self.data = self.overlay.fit(contrast, xyz, fitType == 'full')


class TimeSeriesPanel(plotpanel.PlotPanel):
    """A panel with a :mod:`matplotlib` canvas embedded within.

    The volume data for each of the overlay objects in the
    :class:`.OverlayList`, at the current :attr:`.DisplayContext.location`
    is plotted on the canvas.
    """

    
    usePixdim      = props.Boolean(default=False)
    showCurrent    = props.Boolean(default=True)
    showAllCurrent = props.Boolean(default=False)
    plotMode       = props.Choice(
        ('normal', 'demean', 'normalise', 'percentChange'),
        labels=[strings.choices['TimeSeriesPanel.plotMode.normal'],
                strings.choices['TimeSeriesPanel.plotMode.demean'],
                strings.choices['TimeSeriesPanel.plotMode.normalise'],
                strings.choices['TimeSeriesPanel.plotMode.percentChange']])

    currentColour    = copy.copy(TimeSeries.colour)
    currentAlpha     = copy.copy(TimeSeries.alpha)
    currentLineWidth = copy.copy(TimeSeries.lineWidth)
    currentLineStyle = copy.copy(TimeSeries.lineStyle)


    def __init__(self, parent, overlayList, displayCtx):

        self.currentColour    = (0, 0, 0)
        self.currentAlpha     = 1
        self.currentLineWidth = 1
        self.currentLineStyle = '-'

        actionz = {
            'toggleTimeSeriesList'    : lambda *a: self.togglePanel(
                fslcontrols.TimeSeriesListPanel,    self, location=wx.TOP),
            'toggleTimeSeriesControl' : lambda *a: self.togglePanel(
                fslcontrols.TimeSeriesControlPanel, self, location=wx.TOP) 
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz=actionz)

        figure = self.getFigure()

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        overlayList.addListener('overlays',
                                self._name,
                                self.__overlaysChanged)        
 
        displayCtx .addListener('selectedOverlay', self._name, self.draw) 
        displayCtx .addListener('location',        self._name, self.draw)

        self.addListener('plotMode',    self._name, self.draw)
        self.addListener('usePixdim',   self._name, self.draw)
        self.addListener('showCurrent', self._name, self.draw)

        csc = self.__currentSettingsChanged
        self.addListener('showAllCurrent',   self._name, csc)
        self.addListener('currentColour',    self._name, csc)
        self.addListener('currentAlpha',     self._name, csc)
        self.addListener('currentLineWidth', self._name, csc)
        self.addListener('currentLineStyle', self._name, csc)

        self.__currentOverlay = None
        self.__currentTs      = None
        self.__overlayColours = {}
        self.Layout()
        self.draw()

        
    def __currentSettingsChanged(self, *a):
        if self.__currentTs is None:
            return

        tss = [self.__currentTs]
        
        if isinstance(self.__currentTs, FEATTimeSeries):
            tss = self.__currentTs.getModelTimeSeries()

            for ts in tss:

                if ts is self.__currentTs:
                    continue

                # Don't change the colour for associated
                # time courses (e.g. model fits)
                if ts is self.__currentTs:
                    ts.colour = self.currentColour
                    
                ts.alpha     = self.currentAlpha
                ts.lineWidth = self.currentLineWidth
                ts.lineStyle = self.currentLineStyle


    def destroy(self):
        
        self.removeListener('plotMode',    self._name)
        self.removeListener('usePixdim',   self._name)
        self.removeListener('showCurrent', self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        plotpanel.PlotPanel.destroy(self)


    def __overlaysChanged(self, *a):

        self.disableListener('dataSeries', self._name)
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
        self.enableListener('dataSeries', self._name)
        self.draw()


    def __bindCurrentProps(self, ts, bind=True):
        ts.bindProps('colour'   , self, 'currentColour',    unbind=not bind)
        ts.bindProps('alpha'    , self, 'currentAlpha',     unbind=not bind)
        ts.bindProps('lineWidth', self, 'currentLineWidth', unbind=not bind)
        ts.bindProps('lineStyle', self, 'currentLineStyle', unbind=not bind)

        if bind: self.__currentTs.addGlobalListener(   self._name, self.draw)
        else:    self.__currentTs.removeGlobalListener(self._name)


    def __getTimeSeriesLocation(self, overlay):

        x, y, z = self._displayCtx.location.xyz
        opts    = self._displayCtx.getOpts(overlay)

        if not isinstance(overlay, fslimage.Image)        or \
           not isinstance(opts,    fsldisplay.VolumeOpts) or \
           not overlay.is4DImage():
            return None

        vox = opts.transformCoords([[x, y, z]], 'display', 'voxel')[0]
        vox = np.floor(vox)

        if vox[0] < 0                 or \
           vox[1] < 0                 or \
           vox[2] < 0                 or \
           vox[0] >= overlay.shape[0] or \
           vox[1] >= overlay.shape[1] or \
           vox[2] >= overlay.shape[2]:
            return None

        return vox

    def __genTimeSeries(self, overlay, vox):

        if isinstance(overlay, fslfeatimage.FEATImage):
            ts = FEATTimeSeries(self, overlay, vox)
        else:
            ts = TimeSeries(self, overlay, vox)

        ts.colour    = self.currentColour
        ts.alpha     = self.currentAlpha
        ts.lineWidth = self.currentLineWidth
        ts.lineStyle = self.currentLineStyle
        ts.label     = None            
                
        return ts
            
        
    def __calcCurrent(self):

        prevTs      = self.__currentTs
        prevOverlay = self.__currentOverlay

        if prevTs is not None:
            self.__bindCurrentProps(prevTs, False)

        self.__currentTs      = None
        self.__currentOverlay = None

        if len(self._overlayList) == 0:
            return

        overlay = self._displayCtx.getSelectedOverlay()
        vox     = self.__getTimeSeriesLocation(overlay)

        if vox is None:
            return

        if overlay is prevOverlay:
            self.__currentOverlay = prevOverlay
            self.__currentTs      = prevTs
            prevTs.update(vox)

        else:
            ts                    = self.__genTimeSeries(overlay, vox)
            self.__currentTs      = ts
            self.__currentOverlay = overlay

        self.__bindCurrentProps(self.__currentTs)

        
    def getCurrent(self):
        return self.__currentTs


    def draw(self, *a):

        self.__calcCurrent()
        current = self.__currentTs

        if self.showCurrent:

            extras      = []
            currOverlay = None

            if current is not None:
                if isinstance(current, FEATTimeSeries):
                    extras = current.getModelTimeSeries()
                else:
                    extras = [current]

                currOverlay = current.overlay

            if self.showAllCurrent:
                
                overlays = [o for o in self._overlayList
                            if o is not currOverlay]

                # Remove overlays for which the
                # current location is out of bounds
                locs   = map(self.__getTimeSeriesLocation, overlays)
                locovl = filter(lambda (l, o): l is not None,
                                zip(locs, overlays))
                
                if len(locovl) > 0:
                    locs, overlays = zip(*locovl)

                    tss = map(self.__genTimeSeries, overlays, locs)

                    extras.extend([ts for ts in tss if ts is not None])
                    
                    for ts in tss:
                        ts.alpha     = 1
                        ts.lineWidth = 0.5

                        # Use a random colour for each overlay,
                        # but use the same random colour each time
                        colour = self.__overlayColours.get(
                            ts.overlay,
                            fslcmaps.randomBrightColour())
                        
                        ts.colour = colour
                        self.__overlayColours[ts.overlay] = colour
                        
                        if isinstance(ts, FEATTimeSeries):
                            extras.extend(ts.getModelTimeSeries())
                
            self.drawDataSeries(extras)
        else:
            self.drawDataSeries()
