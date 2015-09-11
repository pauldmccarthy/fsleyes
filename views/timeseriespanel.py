#!/usr/bin/env python
#
# timeseriespanel.py - A panel which plots time series/volume data from a
# collection of overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesPanel`, which is a *FSLeyes
view* for displaying time series data from :class:`.Image` overlays. A
``TimeSeriesPanel`` looks something like the following:

.. image:: images/timeseriespanel.png
   :scale: 50%
   :align: center


The following :class:`.DataSeries` sub-classes are used by the
:class:`TimeSeriesPanel` (see the :class:`.PlotPanel` documentation for more
details):

.. autosummary::
   :nosignatures:

   TimeSeries
   FEATTimeSeries
"""


import copy
import logging

import wx

import numpy as np

import                               props

import                               plotpanel
import fsl.data.featimage         as fslfeatimage
import fsl.data.image             as fslimage
import fsl.fsleyes.displaycontext as fsldisplay
import fsl.fsleyes.colourmaps     as fslcmaps
import fsl.fsleyes.controls       as fslcontrols


log = logging.getLogger(__name__)


class TimeSeries(plotpanel.DataSeries):
    """Encapsulates time series data from a specific voxel in an
    :class:`.Image` overlay.
    """

    
    def __init__(self, tsPanel, overlay, coords):
        """Create a ``TimeSeries`` instane.

        :arg tsPanel: The :class:`TimeSeriesPanel` which owns this
                      ``TimeSeries``.

        :arg overlay: The :class:`.Image` instance to extract the data from.

        :arg coords:  The voxel coordinates of the time series.
        """
        plotpanel.DataSeries.__init__(self, overlay)

        self.tsPanel = tsPanel
        self.coords  = map(int, coords)
        self.data    = overlay.data[coords[0], coords[1], coords[2], :]


    def __copy__(self):
        """Copy operator, creates and returns a copy of this ``TimeSeries``
        instance.
        """
        return type(self)(self.tsPanel, self.overlay, self.coords)

        
    def update(self, coords):
        """Updates the voxel coordinates and time series data encapsulated
        by this ``TimeSeries``.

        .. warning:: This method is only intended for use on the *current*
                     ``TimeSeriesPanel`` series, not for time series instances
                     which have been added to the :attr:`.PlotPanel.dataSeries`
                     list.
        
                     It is used by the :class:`TimeSeriesPanel` so that
                     ``TimeSeries`` instances do not have to constantly be
                     destroyed/recreated whenever the
                     :attr:`.DisplayContext.location` changes.
        """
        
        coords = map(int, coords)
        if coords == self.coords:
            return False
        
        self.coords = coords
        self.data   = self.overlay.data[coords[0], coords[1], coords[2], :]
        return True

        
    def getData(self, xdata=None, ydata=None):
        """Overrides :meth:`.DataSeries.getData` Returns the data associated
        with this ``TimeSeries`` instance.

        The ``xdata`` and ``ydata`` arguments may be used by subclasses to
        override the x/y data in the event that they have already performed
        some processing on the data.
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
    """A :class:`TimeSeries` class for use with :class:`FEATImage` instances,
    containing some extra FEAT specific options.

    The ``FEATTimeSeries`` class acts as a container for several
    ``TimeSeries`` instances, each of which represent some part of a FEAT
    analysis. Therefore, the data returned by a call to
    :meth:`.TimeSeries.getData` on a ``FEATTimeSeries`` instance should not
    be plotted.

    Instead, the :meth:`getModelTimeSeries` method should be used to retrieve
    a list of all the ``TimeSeries`` instances which are associated with the
    ``FEATTimeSeries`` instance - all of these ``TimeSeries`` instances should
    be plotted instead.

    For example, if the :attr:`plotData` and :attr:`plotFullModelFit` settings
    are ``True``, the :meth:`getModelTimeSeries` method will return a list
    containing two ``TimeSeries`` instances - one which will return the FEAT
    analysis input data, and another which will return the full model fit, for
    the voxel in question.


    .. note:: The ``getData`` method of a ``FEATTimeSeries`` instance will
              return the FEAT input data; therefore, when :attr:`plotData` is
              ``True``, the ``FEATTimeSeries`` instance will itself be included
              in the list returned by :meth:`getModelTimeSeries`.

    
    The following classes are used to represent the various parts of a FEAT
    analysis:

    .. autosummary::
       :nosignatures:
    
       FEATEVTimeSeries
       FEATResidualTimeSeries
       FEATPartialFitTimeSeries
       FEATModelFitTimeSeries
    """


    plotData = props.Boolean(default=True)
    """If ``True``, the FEAT input data is plotted. """

    
    plotFullModelFit = props.Boolean(default=True)
    """If ``True``, the FEAT full model fit is plotted. """

    
    plotResiduals = props.Boolean(default=False)
    """If ``True``, the FEAT model residuals are plotted. """

    
    plotEVs = props.List(props.Boolean(default=False))
    """A list of ``Boolean`` properties, one for each EV in the FEAT analysis.
    For elements that are ``True``, the corresponding FEAT EV time course is
    plotted.
    """

    
    plotPEFits = props.List(props.Boolean(default=False))
    """A list of ``Boolean`` properties, one for each EV in the FEAT analysis.
    For elements that are ``True``, the model fit for the corresponding FEAT
    EV is plotted.    
    """

    
    plotCOPEFits = props.List(props.Boolean(default=False))
    """A list of ``Boolean`` properties, one for each EV in the FEAT analysis.
    For elements that are ``True``, the model fit for the corresponding FEAT
    contrast is plotted.    
    """ 

    
    plotPartial = props.Choice()
    """Plot the raw data, after regression against a chosen EV or contrast.
    The options are populated in the :meth:`__init__` method.
    """
    

    def __init__(self, *args, **kwargs):
        """Create a ``FEATTimeSeries``.

        All arguments are passed through to the :class:`TimeSeries`
        constructor.
        """
        
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

        self.getProp('plotPartial').setChoices(reduceOpts, instance=self)

        for i in range(numEVs):
            self.plotPEFits.append(False)
            self.plotEVs   .append(False)

        for i in range(numCOPEs):
            self.plotCOPEFits.append(False) 

        self.__fullModelTs =  None
        self.__partialTs   =  None
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
        self.addListener('plotPartial',
                         self.name,
                         self.__plotPartialChanged)

        self.addListener('plotEVs',      self.name, self.__plotEVChanged)
        self.addListener('plotPEFits',   self.name, self.__plotPEFitChanged)
        self.addListener('plotCOPEFits', self.name, self.__plotCOPEFitChanged)

        # plotFullModelFit defaults to True, so
        # force the model fit ts creation here
        self.__plotFullModelFitChanged()


    def __copy__(self):
        """Copy operator for a ``FEATTimeSeries`` instance."""
        
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
        copy.plotPartial      = self.plotPartial
        copy.plotResiduals    = self.plotResiduals

        return copy
 

    def getModelTimeSeries(self):
        """Returns a list containing all of the ``TimeSeries`` instances
        which should be plotted in place of this ``FEATTimeSeries``.
        """
        
        
        modelts = []

        if self.plotData:              modelts.append(self)
        if self.plotFullModelFit:      modelts.append(self.__fullModelTs)
        if self.plotResiduals:         modelts.append(self.__resTs)
        if self.plotPartial != 'none': modelts.append(self.__partialTs)
        
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


    def update(self, coords):
        """Overrides :meth:`TimeSeries.update`.

        Updates the coordinates and data associated wsith this
        ``FEATTimeSeries`` instance.
        """
        
        if not TimeSeries.update(self, coords):
            return False
            
        for modelTs in self.getModelTimeSeries():
            if modelTs is self:
                continue
            modelTs.update(coords)

        return True


    def __getContrast(self, fitType, idx):
        """Returns a contrast vector for the given model fit type, and index.

        :arg fitType: either ``'full'``, ``'pe'``, or ``'cope'``. If
                      ``'full'``, the ``idx`` argument is ignored.

        :arg idx:     The EV or contrast index for ``'pe'`` or ``'cope'`` model
                      fits.
        """

        if fitType == 'full':
            return [1] * self.overlay.numEVs()
        elif fitType == 'pe':
            con      = [0] * self.overlay.numEVs()
            con[idx] = 1
            return con
        elif fitType == 'cope':
            return self.overlay.contrasts()[idx]

        
    def __createModelTs(self, tsType, *args, **kwargs):
        """Creates a ``TimeSeries`` instance of the given ``tsType``, and
        sets its display settings  according to those of this
        ``FEATTimeSeries``.

        :arg tsType: The type to create, e.g. :class:`FEATModelFitTimeSeries`,
                     :class:`FEATEVTimeSeries`, etc.

        :arg args:   Passed to the ``tsType`` constructor.

        :arg kwargs: Passed to the ``tsType`` constructor.
        """

        ts = tsType(self.tsPanel, self.overlay, self.coords, *args, **kwargs)

        ts.alpha     = self.alpha
        ts.label     = self.label
        ts.lineWidth = self.lineWidth
        ts.lineStyle = self.lineStyle

        if   isinstance(ts, FEATPartialFitTimeSeries):
            ts.colour = (0, 0.6, 0.6)
        elif isinstance(ts, FEATResidualTimeSeries):
            ts.colour = (0.8, 0.4, 0)
        elif isinstance(ts, FEATEVTimeSeries):
            ts.colour = (0, 0.7, 0.35)
        elif isinstance(ts, FEATModelFitTimeSeries):
            if   ts.fitType == 'full': ts.colour = (0,   0, 1)
            elif ts.fitType == 'cope': ts.colour = (0,   1, 0)
            elif ts.fitType == 'pe':   ts.colour = (0.7, 0, 0)

        return ts


    def __plotPartialChanged(self, *a):
        """Called when the :attr:`plotPartial` setting changes.

        If necessary, creates and caches a :class:`FEATPartialFitTimeSeries`
        instance.
        """
            
        partial = self.plotPartial

        if partial == 'none' and self.__partialTs is not None:
            self.__partialTs = None
            return

        partial = partial.split()[0]

        # fitType is either 'cope' or 'pe'
        fitType = partial[:-1].lower()
        idx     = int(partial[-1]) - 1

        self.__partialTs = self.__createModelTs(
            FEATPartialFitTimeSeries,
            self.__getContrast(fitType, idx),
            fitType,
            idx) 


    def __plotResidualsChanged(self, *a):
        """Called when the :attr:`plotResiduals` setting changes.

        If necessary, creates and caches a :class:`FEATResidualTimeSeries`
        instance.
        """ 
        
        if not self.plotResiduals:
            self.__resTs = None
            return

        self.__resTs = self.__createModelTs(FEATResidualTimeSeries)


    def __plotEVChanged(self, *a):
        """Called when the :attr:`plotEVs` setting changes.

        If necessary, creates and caches one or more :class:`FEATEVTimeSeries`
        instances.
        """ 

        for evnum, plotEV in enumerate(self.plotEVs):

            if not self.plotEVs[evnum]:
                self.__evTs[evnum] = None
                
            elif self.__evTs[evnum] is None:
                self.__evTs[evnum] = self.__createModelTs(
                    FEATEVTimeSeries, evnum)
            
    
    def __plotCOPEFitChanged(self, *a):
        """Called when the :attr:`plotCOPEFits` setting changes.

        If necessary, creates and caches one or more
        :class:`FEATModelFitTimeSeries` instances.
        """ 

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
        """Called when the :attr:`plotPEFits` setting changes.

        If necessary, creates and caches one or more
        :class:`FEATModelFitTimeSeries` instances.
        """         

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
        """Called when the :attr:`plotFullModelFit` setting changes.

        If necessary, creates and caches a
        :class:`FEATModelFitTimeSeries` instance.
        """
        
        if not self.plotFullModelFit:
            self.__fullModelTs = None
            return

        self.__fullModelTs = self.__createModelTs(
            FEATModelFitTimeSeries, self.__getContrast('full', -1), 'full', -1)


class FEATPartialFitTimeSeries(TimeSeries):
    """A :class:`TimeSeries` class which represents the partial model fit
    of an EV or contrast from a FEAT analysis. Instances of this class
    are created by the :class:`FEATTimeSeries` class.
    """
    def __init__(self, tsPanel, overlay, coords, contrast, fitType, idx):
        """Create a ``FEATPartialFitTimeSeries``.

        :arg tsPanel:  The :class:`TimeSeriesPanel` that owns this
                       ``FEATPartialFitTimeSeries`` instance.
        
        :arg overlay:  A :class:`.FEATImage` overlay.
        
        :arg coords:   Voxel coordinates.
        
        :arg contrast: The contrast vector to calculate the partial model
                       fit for.
        
        :arg fitType:  The model fit type, either ``'full'``, ``'pe'`` or
                       ``'cope'``.
        
        :arg idx:      If the model fit type is ``'pe'`` or ``'cope'``,
                       the EV/contrast index.
        """
        TimeSeries.__init__(self, tsPanel, overlay, coords)

        self.contrast = contrast
        self.fitType  = fitType
        self.idx      = idx

        
    def getData(self):
        """Returns the partial model fit for the voxel and model fit type
        specified in the constructop.

        See the :meth:`.FEATImage.partialFit` method.
        """
        
        data = self.overlay.partialFit(self.contrast, self.coords, False)
        return TimeSeries.getData(self, ydata=data)

    
class FEATEVTimeSeries(TimeSeries):
    """A :class:`TimeSeries` class which represents the time course of an
    EV from a FEAT analysis. Instances of this class are created by the
    :class:`FEATTimeSeries` class.
    """
    
    def __init__(self, tsPanel, overlay, coords, idx):
        """Create a ``FEATEVTimeSeries``.

        :arg tsPanel:  The :class:`TimeSeriesPanel` that owns this
                       ``FEATEVTimeSeries`` instance.
        
        :arg overlay:  A :class:`.FEATImage` overlay.
        
        :arg coords:   Voxel coordinates.

        :arg idx:      The EV index.
        """
        TimeSeries.__init__(self, tsPanel, overlay, coords)
        self.idx = idx

        
    def getData(self):
        """Returns the time course of the EV specified in the constructor. """
        data = self.overlay.getDesign()[:, self.idx]
        return TimeSeries.getData(self, ydata=data)
    

class FEATResidualTimeSeries(TimeSeries):
    """A :class:`TimeSeries` class which represents the time course of the
    residuals from a FEAT analysis. Instances of this class are created by
    the :class:`FEATTimeSeries` class.
    """

    
    def getData(self):
        """Returns the residuals for the voxel specified in the constructor.
        """
        x, y, z = self.coords
        data    = self.overlay.getResiduals().data[x, y, z, :]
        
        return TimeSeries.getData(self, ydata=np.array(data))
            

class FEATModelFitTimeSeries(TimeSeries):
    """A :class:`TimeSeries` class which represents the time course for 
    a model fit from a FEAT analysis. Instances of this class are created by
    the :class:`FEATTimeSeries` class.
    """ 

    def __init__(self, tsPanel, overlay, coords, contrast, fitType, idx):
        """Create a ``FEATModelFitTimeSeries``.
        
        :arg tsPanel:  The :class:`TimeSeriesPanel` that owns this
                       ``FEATModelFitTimeSeries`` instance.
        
        :arg overlay:  A :class:`.FEATImage` overlay.
        
        :arg coords:   Voxel coordinates.
        
        :arg contrast: The contrast vector to calculate the partial model
                       fit for.
        
        :arg fitType:  The model fit type, either ``'full'``, ``'pe'`` or
                       ``'cope'``.
        
        :arg idx:      If the model fit type is ``'pe'`` or ``'cope'``,
                       the EV/contrast index.
        """
        
        if fitType not in ('full', 'cope', 'pe'):
            raise ValueError('Unknown model fit type {}'.format(fitType))
        
        TimeSeries.__init__(self, tsPanel, overlay, coords)
        self.fitType  = fitType
        self.idx      = idx
        self.contrast = contrast
        self.__updateModelFit()

        
    def update(self, coords):
        """Overrides :meth:`TimeSeries.update`.

        Updates the coordinates and the data encapsulated by this
        ``FEATModelFitTimeSeries``.
        """
        if not TimeSeries.update(self, coords):
            return
        self.updateModelFit()
        

    def __updateModelFit(self):
        """Called by :meth:`update`, and in the constructor.  Updates the model
        fit. See the :meth:`.FEATImage.fit` method.
        """

        fitType   = self.fitType
        contrast  = self.contrast
        xyz       = self.coords
        self.data = self.overlay.fit(contrast, xyz, fitType == 'full')


class TimeSeriesPanel(plotpanel.PlotPanel):
    """A :class:`.PlotPanel` which plots time series data from
    :class:`.Image` overlays.

    A ``TimeSeriesPanel`` plots one or more :class:`TimeSeries` instances,
    which encapsulate time series data for a voxel from a :class:`.Image`
    overlay.

    
    **The current time course**

    
    By default, the ``TimeSeriesPanel`` plots the time series of the current
    voxel from the currently selected overlay, if it is an :class:`.Image`
    instance.  The selected overlay and voxel are determined from the
    :attr:`.DisplayContext.selectedOverlay` and
    :attr:`.DisplayContext.location` respectively. This time series is
    referred to as the *current* time course. This behaviour can be disabled
    with the :attr:`showCurrent` setting. If the :attr:`showAllCurrent`
    setting is ``True``, the current time course for all compatible overlays
    in the :class:`.OverlayList` is plotted.
    

    Other time courses can be *held* by adding them to the
    :attr:`.PlotPanel.dataSeries` list - the :class:`.TimeSeriesListPanel`
    provides the user with the ability to add/remove time courses from the
    ``dataSeries`` list.


    **Control panels**

    
    Some *FSLeyes control* panels are associated with the
    :class:`.TimeSeriesPanel`:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.controls.timeserieslistpanel.TimeSeriesListPanel
       ~fsl.fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel

    
    The ``TimeSeriesPanel`` defines some :mod:`.actions`, allowing the user
    to show/hide these control panels (see the :meth:`.ViewPanel.togglePanel`
    method):

    =========================== ===============================================
    ``toggleTimeSeriesList``    Shows/hides a :class:`.TimeSeriesListPanel`.
    ``toggleTimeSeriesControl`` Shows/hides a :class:`.TimeSeriesControlPanel`.
    =========================== ===============================================

    New ``TimeSeriesPanel`` instances will display a ``TimeSeriesListPanel``
    and a ``TimeSeriesControlPanel`` by default.


    **FEATures**


    The ``TimeSeriesPanel`` has some extra functionality for
    :class:`.FEATImage` overlays. For these overlays, a :class:`FEATTimeSeries`
    instance is plotted, instead of a regular :class:`TimeSeries` instance. The
    ``FEATTimeSeries`` class, in turn, has the ability to generate more
    ``TimeSeries`` instances which represent various aspects of the FEAT model
    fit. See the :class:`FEATTimeSeries` and the
    :class:`.TimeSeriesControlPanel` classes for more details.
    """

    
    usePixdim = props.Boolean(default=False)
    """If ``True``, the X axis data is scaled by the pixdim value of the
    selected overlay (which, for FMRI time series data is typically set
    to the TR time).
    """

    
    showCurrent = props.Boolean(default=True)
    """If ``True``, the time course for the current voxel of the currently
    selected overlay is plotted.
    """

    
    showAllCurrent = props.Boolean(default=False)
    """If ``True``, the time courses from the current
    :attr:`.DisplayContext.location` for all compatible overlays in the
    :class:`.OverlayList` are plotted.
    """

    
    plotMode = props.Choice(('normal', 'demean', 'normalise', 'percentChange'))
    """Options to scale/offset the plotted time courses.

    ================= =======================================================
    ``normal``        The data is plotted with no modifications
    ``demean``        The data is demeaned (i.e. plotted with a mean of 0)
    ``normalise``     The data is normalised to lie in the range ``[-1, 1]``.
    ``percentChange`` The data is scaled to percent changed
    ================= =======================================================
    """

    currentColour = copy.copy(TimeSeries.colour)
    """Colour to use for the current time course. """

    
    currentAlpha = copy.copy(TimeSeries.alpha)
    """Transparency to use for the current time course. """

    
    currentLineWidth = copy.copy(TimeSeries.lineWidth)
    """Line width to use for the current time course. """

    
    currentLineStyle = copy.copy(TimeSeries.lineStyle)
    """Line style to use for the current time course. """


    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``TimeSeriesPanel``.

        :arg parent:      A :mod:`wx` parent object.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        """

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
        self.addListener('currentColour',    self._name, csc)
        self.addListener('currentAlpha',     self._name, csc)
        self.addListener('currentLineWidth', self._name, csc)
        self.addListener('currentLineStyle', self._name, csc)

        self.__currentOverlay = None
        self.__currentTs      = None
        self.__overlayColours = {}

        def addPanels():
            self.run('toggleTimeSeriesControl') 
            self.run('toggleTimeSeriesList') 

        wx.CallAfter(addPanels)

        self.draw()


    def destroy(self):
        """Removes some listeners, and calls the :meth:`.PlotPanel.destroy`
        method.
        """
        
        self.removeListener('plotMode',    self._name)
        self.removeListener('usePixdim',   self._name)
        self.removeListener('showCurrent', self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        plotpanel.PlotPanel.destroy(self) 

        
    def getCurrent(self):
        """Returns the :class:`TimeSeries` instance for the current time
        course. If :attr:`showCurrent` is ``False``, or the currently
        selected overlay is not a :class:`.Image` (see
        :attr:`.DisplayContext.selectedOverlay`) this method will return
        ``None``.
        """
        
        return self.__currentTs


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Generates the current time
        course(s) if necessary, and calls the :meth:`.PlotPanel.drawDataSeries`
        method.
        """

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

        
    def __currentSettingsChanged(self, *a):
        """Called when the settings controlling the display of the current time
        course(s) changes.  If the current time course is a
        :class:`FEATTimeSeries`, the display settings are propagated to all of
        its associated time courses (see the
        :meth:`FEATTimeSeries.getModelTimeSeries` method).
        """
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



    def __overlaysChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Makes sure
        that there are no :class:`TimeSeries` instances in the
        :attr:`.PlotPanel.dataSeries` list which refer to overlays that
        no longer exist.
        """

        self.disableListener('dataSeries', self._name)
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
        self.enableListener('dataSeries', self._name)
        self.draw()


    def __bindCurrentProps(self, ts, bind=True):
        """Binds or unbinds the properties of the given :class:`TimeSeries`
        instance with the current display settings (e.g.
        :attr:`currentColour`, :attr:`currentAlpha`, etc).
        """
        ts.bindProps('colour'   , self, 'currentColour',    unbind=not bind)
        ts.bindProps('alpha'    , self, 'currentAlpha',     unbind=not bind)
        ts.bindProps('lineWidth', self, 'currentLineWidth', unbind=not bind)
        ts.bindProps('lineStyle', self, 'currentLineStyle', unbind=not bind)

        if bind: self.__currentTs.addGlobalListener(   self._name, self.draw)
        else:    self.__currentTs.removeGlobalListener(self._name)


    def __getTimeSeriesLocation(self, overlay):
        """Calculates and returns the voxel coordinates corresponding to the
        current :attr:`.DisplayContext.location` for the specified ``overlay``.

        Returns ``None`` if the given overlay is not a 4D :class:`.Image`
        which is being displayed with a :class:`.VolumeOpts` instance, or if
        the current location is outside of the image bounds.
        """

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
        """Creates and returns a :class:`TimeSeries` or :class:`FEATTimeSeries`
        instance for the specified voxel of the specified overlay.
        """

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
        """Called by the :meth:`draw` method. Makes sure that the current
        time course(s) is/are up to date.
        """

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
